from domain.ports import LeaveBalancePort,TicketCreationPort
from domain.tools.clerk_tool import make_get_leave_balance_tool,make_ticket_creation_tool
from domain.prompts.clerk_prompt import Clerk_Classification_prompt,Clerk_Inner_Model_Prompt,Clerk_Final_Response_Prompt
from domain.entities import TicketCreation, TicketCreationClassification, GetBalanceClassification, GeneralInformationClassification
from application.states import ClerkClassificationState, ClerkState
from langchain_core.language_models.chat_models import BaseChatModel
from langgraph.graph import END,StateGraph,START
from collections import deque
from langchain_core.messages import AIMessage
try:
    from IPython.display import Image,display
except ImportError:
    Image=None
    display=None
from infrastructure.redis.redis_client import save_agent_state_for_final_response,get_agent_state_for_final_response,save_agent_state_for_hitl_intervention
from domain.entities import AgentState
from infrastructure.redis.redis_config import get_async_redis_client
from infrastructure.socket.socket_manager import broadcast_hitl_event
import json

#Clerk Agent Implementation
class ClerkAgent:
    def __init__(self, llm_model:BaseChatModel, leave_balance_port:LeaveBalancePort, ticket_creation_port:TicketCreationPort):
        self.llm_model=llm_model
        self.leave_balance_port=leave_balance_port
        self.ticket_creation_port=ticket_creation_port

    # The outer model node takes the user's query 
    # classifies it into one or more tasks for the inner model to execute. 
    # It also initializes the agent's state with the original user query and an empty message history.
    def Clerk_Outer_Model_Node(self, state: ClerkState) -> dict:
        try:
            formatted_prompt = Clerk_Classification_prompt.format_messages(query=state.user_query.query)
            response = self.llm_model.invoke(list(state.messages) + formatted_prompt)

            raw = response.content.strip()

            if raw.startswith("```"):
                lines = [l for l in raw.split("\n") if not l.strip().startswith("```")]
                raw = "\n".join(lines).strip()

            parsed = json.loads(raw)

            if isinstance(parsed, dict):
                parsed = [parsed]

            tasks = [self._parse_clerk_task(t) for t in parsed]

            return {
                "messages": [AIMessage(content=response.content)],
                "pending_tasks": deque(tasks)
            }
        except Exception as e:
            print(f"[Clerk] Outer model error: {type(e).__name__}: {e}")
            return {"pending_tasks": deque()}


    #Clerk Decision node
    def Clerk_Decision_Node(self, state: ClerkState) -> dict:
        if state.hitl_state:
            next_step = "hitl"
        elif state.pending_tasks:
            next_step = "inner"
        else:
            next_step = "final"
        return {"next_step": next_step}


    #clerk inner model node takes the current task from the pending_tasks queue
    # generates a response that includes the details needed to execute the task. 
    # It updates the agent's state with the new messages, the final response for the current task, and the remaining pending tasks.
    def Clerk_Inner_Model_Node(self, state: ClerkState) -> dict:
        try:
            pending = deque(state.pending_tasks)
            current_task = pending.popleft()

            formatted_prompt = Clerk_Inner_Model_Prompt.format_messages(
                current_task=current_task.model_dump(),
                user_query=state.user_query.query
            )
            response = self.llm_model.invoke(list(state.messages) + formatted_prompt)

            raw = response.content.strip()

            if raw.startswith("```"):
                lines = [l for l in raw.split("\n") if not l.strip().startswith("```")]
                raw = "\n".join(lines).strip()

            parsed = json.loads(raw)
            result = self._parse_clerk_task(parsed)

            final_response = list(state.final_response or [])
            final_response.append(result)

            return {
                "messages": [AIMessage(content=response.content)],
                "final_response": final_response,
                "pending_tasks": pending
            }
        except Exception as e:
            print(f"[Clerk] Inner model error: {type(e).__name__}: {e}")
            drained = deque(state.pending_tasks)
            if drained:
                drained.popleft()
            return {
                "final_response": state.final_response,
                "pending_tasks": drained
            }


    # This method executes the current task using the appropriate tool based on the action type.
    def _parse_clerk_task(self, data: dict):
        action = data.get("action")
        if action == "ticket_creation":
            if data.get("details") is not None:
                return TicketCreationClassification(**data)
            return TicketCreationClassification(action="ticket_creation", details=None)
        elif action == "get_balance":
            return GetBalanceClassification(**data)
        elif action == "general_information":
            return GeneralInformationClassification(**data)
        else:
            return GetBalanceClassification(action="get_balance", details=None)


    # The tool execution node checks the final_response for the current task 
    #  executes the corresponding tool based on the action type.
    def Clerk_Tool_Execution_Node(self, state: ClerkState) -> dict:
        if not state.final_response:
            return {}

        tool_execution: ClerkClassificationState = state.final_response[-1]

        if tool_execution.action == "get_balance":
            already_executed = any(r.get("action") == "get_balance" for r in state.tool_results)
            if not already_executed:
                counter = 3
                while counter > 0:
                    try:
                        leave_balance_tool = make_get_leave_balance_tool(self.leave_balance_port, state.user_query.auth_token)
                        leave_balance: int = leave_balance_tool.invoke({})
                        state.tool_results.append({
                            "action": "get_balance",
                            "success": True,
                            "data": {"leave_balance": leave_balance},
                            "error": None,
                        })
                        break
                    except Exception as e:
                        counter -= 1
                        if counter == 0:
                            state.tool_results.append({
                                "action": "get_balance",
                                "success": False,
                                "data": None,
                                "error": str(e),
                            })

        elif tool_execution.action == "ticket_creation":
            counter = 3
            while counter > 0:
                try:
                    already_rejected = (
                        tool_execution.details is not None
                        and tool_execution.details.accepted is False
                    )

                    if not already_rejected:
                        if tool_execution.details is None or not all([
                            tool_execution.details.ticket_type,
                            tool_execution.details.subject,
                            tool_execution.details.description
                        ]):
                            state.hitl_state.append(tool_execution)
                            return {
                                "hitl_state": state.hitl_state,
                                "final_response": state.final_response,
                                "messages": [AIMessage(content="Insufficient details for ticket creation. Need HITL intervention.")],
                            }

                        elif tool_execution.details.ticket_type == "leave" and tool_execution.details.leave_days is None:
                            state.hitl_state.append(tool_execution)
                            return {
                                "hitl_state": state.hitl_state,
                                "final_response": state.final_response,
                                "messages": [AIMessage(content="Insufficient details for leave ticket creation. Need HITL intervention.")],
                            }

                        elif (tool_execution.details.ticket_type in ["leave", "complaint"]) and tool_execution.details.accepted is None:
                            state.hitl_state.append(tool_execution)
                            return {
                                "hitl_state": state.hitl_state,
                                "final_response": state.final_response,
                                "messages": [AIMessage(content="Need Confirmation from user for creating a complaint or leave ticket. Need HITL intervention.")],
                            }

                    ticket_creation_date = TicketCreation(
                        ticket_type=tool_execution.details.ticket_type,
                        subject=tool_execution.details.subject,
                        description=tool_execution.details.description,
                        status="in_progress",
                        leave_days=tool_execution.details.leave_days,
                        accepted=tool_execution.details.accepted
                    )
                    if ticket_creation_date.accepted is False:
                        state.tool_results.append({
                            "action": "ticket_creation",
                            "success": False,
                            "data": None,
                            "error": "User rejected the ticket creation.",
                        })
                    else:
                        ticket_creation_tool = make_ticket_creation_tool(self.ticket_creation_port, ticket_creation_date, state.user_query.auth_token)
                        response: bool = ticket_creation_tool.invoke({})
                        state.tool_results.append({
                            "action": "ticket_creation",
                            "success": response,
                            "data": tool_execution.details if response else None,
                            "error": None if response else "Ticket creation failed due to unknown error.",
                        })
                    break

                except Exception as e:
                    counter -= 1
                    if counter == 0:
                        state.tool_results.append({
                            "action": "ticket_creation",
                            "success": False,
                            "data": None,
                            "error": str(e),
                        })

        return {"tool_results": state.tool_results}

    # This method handles the HITL intervention by sending the HITL task details to the frontend,
    #  waiting for the human response, and then updating the agent's state with the response to resume task execution.
    async def hitl_intervention_node(self, state: ClerkState) -> dict:
        user_id = state.user_query.user_id
        conversation_id = state.user_query.conversation_id

        hitl_data = state.hitl_state.popleft()

        event_payload = {
            "user_id": user_id,
            "conversation_id": conversation_id,
            "agent": "Clerk",
            "hitl_task": hitl_data.model_dump()
        }

        save_agent_state_for_hitl_intervention(AgentState(
            user_id=user_id,
            key=conversation_id,
            agent_name="Clerk",
            state={"hitl_task": hitl_data.model_dump()}
        ))

        await broadcast_hitl_event(
            user_id=user_id,
            conversation_id=conversation_id,
            agent_name="Clerk",
            event_data=event_payload
        )

        redis = get_async_redis_client()
        pubsub = redis.pubsub()
        response_channel = f"HITL_Response_Channel:{user_id}:{conversation_id}:Clerk"
        await pubsub.subscribe(response_channel)

        try:
            async for message in pubsub.listen():
                if message["type"] == "message":
                    response_payload = json.loads(message["data"])

                    await pubsub.unsubscribe(response_channel)

                    if not state.final_response:
                        return {
                            "hitl_state": state.hitl_state,
                            "messages": [AIMessage(content="HITL error: final_response was empty when trying to update task.")],
                        }

                    result: ClerkClassificationState = state.final_response.pop()

                    detail_keys = {"ticket_type", "subject", "description", "leave_days", "accepted", "status"}
                    updated_details = {k: v for k, v in response_payload.items() if k in detail_keys}

                    status_value = str(response_payload.get("status", "")).strip().lower()
                    detail_value = response_payload.get("detail")
                    is_rejection = (
                        response_payload.get("accepted") is False
                        or detail_value is False
                        or status_value in {"rejected", "reject", "cancelled", "canceled", "cancel"}
                    )

                    if is_rejection:
                        updated_details["accepted"] = False

                    if updated_details and hasattr(result, "details"):
                        if result.details is not None:
                            
                            result = result.model_copy(update={"details": result.details.model_copy(update=updated_details)})
                        elif is_rejection:
            
                            from domain.entities import TicketCreation
                            minimal_details = TicketCreation(
                                ticket_type=updated_details.get("ticket_type") or "help",
                                subject=updated_details.get("subject") or "Cancelled",
                                description=updated_details.get("description") or "Cancelled by user",
                                status="in_progress",
                                leave_days=updated_details.get("leave_days"),
                                accepted=False,
                            )
                            result = result.model_copy(update={"details": minimal_details})

                    state.final_response.append(result)
                    return {
                        "final_response": state.final_response,
                        "hitl_state": state.hitl_state,
                        "messages": [AIMessage(content="Received HITL response, resuming task execution.")],
                    }
        finally:
            await redis.aclose()

    # The final response node generates the final response to the user after all tasks have been executed. 
    # It compiles the results from the tool executions 
    # formats a response using the final response prompt. 
    def Clerk_Final_Response_Node(self, state: ClerkState) -> dict:
        formatted_prompt = Clerk_Final_Response_Prompt.format_messages(
            final_response=list(state.final_response),
            tool_results=state.tool_results
        )
        counter = 3
        while counter > 0:
            try:
                response = self.llm_model.invoke(list(state.messages) + formatted_prompt)

                user_id = state.user_query.user_id
                conversation_id = state.user_query.conversation_id
                existing = get_agent_state_for_final_response(user_id, conversation_id, "Clerk")

                agent_state = AgentState(
                    user_id=user_id,
                    key=conversation_id,
                    agent_name="Clerk",
                    state={
                        **existing,
                        "status": "completed",
                        "final_response": response.content,
                    }
                )
                save_agent_state_for_final_response(agent_state)
                return {
                    "messages": [AIMessage(content=response.content)],
                    "final_response": deque(),
                }
            except Exception as e:
                print(f"[Clerk] Final response error: {type(e).__name__}: {e}")
                counter -= 1

        return {
            "messages": [AIMessage(content="Sorry, I am unable to generate a response at the moment.")],
        }

    
    def create_clerk_agent_graph(self) -> StateGraph:
        clerk_graph = StateGraph(ClerkState)
        clerk_graph.add_node("clerk_outer_model_node", self.Clerk_Outer_Model_Node)
        clerk_graph.add_node("clerk_decision_node", self.Clerk_Decision_Node)
        clerk_graph.add_node("clerk_inner_model_node", self.Clerk_Inner_Model_Node)
        clerk_graph.add_node("clerk_tool_execution_node", self.Clerk_Tool_Execution_Node)
        clerk_graph.add_node("final_response_node", self.Clerk_Final_Response_Node)
        clerk_graph.add_node("hitl_intervention_node", self.hitl_intervention_node)
        clerk_graph.add_edge(START, "clerk_outer_model_node")
        clerk_graph.add_edge("clerk_outer_model_node", "clerk_decision_node")
        clerk_graph.add_conditional_edges(
            "clerk_decision_node",
            lambda state: state.next_step,
            {
                "inner": "clerk_inner_model_node",
                "final": "final_response_node",
                "hitl": "hitl_intervention_node"
            }
        )
        clerk_graph.add_edge("clerk_inner_model_node", "clerk_tool_execution_node")
        clerk_graph.add_edge("clerk_tool_execution_node", "clerk_decision_node")
        clerk_graph.add_edge("final_response_node", END)
        clerk_graph.add_edge("hitl_intervention_node", "clerk_tool_execution_node")
        return clerk_graph.compile()

    def display_clerk_agent_graph(self, agent: StateGraph):
        png_bytes = agent.get_graph(xray=True).draw_mermaid_png()
        with open("clerk_agent_graph.png", "wb") as f:
            f.write(png_bytes)
        display(Image(png_bytes))