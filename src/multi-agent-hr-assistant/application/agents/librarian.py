from langchain_core.messages import AIMessage
from domain.ports import LibrarianRetrievalPort, LibrarianInsertionPort, LibrarianUpdatePort
from domain.entities import LibrarianTask
from application.states import LibrarianState
from domain.tools.librarian_tool import make_librarian_retrieval_tool, make_librarian_insertion_tool, make_librarian_update_tool
from langchain_core.language_models.chat_models import BaseChatModel
try:
    from IPython.display import Image, display
except ImportError:
    Image = None
    display = None
from langgraph.graph import START, END, StateGraph
from domain.prompts.librarian_prompt import librarianPrompt, LibrarianFinalResponsePrompt
from infrastructure.redis.redis_client import (
    save_agent_state_for_final_response,
    get_agent_state_for_final_response,
    save_agent_state_for_hitl_intervention,
)
from domain.entities import AgentState
from infrastructure.redis.redis_config import get_async_redis_client
from infrastructure.socket.socket_manager import broadcast_hitl_event
import json

#Librarian Agent Implementation
class LibrarianAgent:
    def __init__(
        self,
        llm_model: BaseChatModel,
        retrieval_port: LibrarianRetrievalPort,
        insertion_port: LibrarianInsertionPort,
        update_port: LibrarianUpdatePort,
    ):
        self.llm_model = llm_model
        self.retrieval_tool = make_librarian_retrieval_tool(retrieval_port)
        self.insertion_tool = make_librarian_insertion_tool(insertion_port)
        self.update_tool = make_librarian_update_tool(update_port)

    #Librarian model node takes the user's query and classifies it into one or more tasks for the agent to execute.
    def librarian_model_node(self, state: LibrarianState) -> dict:
        """
        Classifies the user request into one or more LibrarianTask objects by
        invoking the LLM with the librarian prompt and parsing the JSON reply.
        """
        try:
            formatted_prompt = librarianPrompt.format_messages(
                user_query=state.user_query.query,
                isAdmin=state.user_query.isAdmin,
                UploadedText=state.user_query.UploadedText,
            )

            response = self.llm_model.invoke(list(state.messages) + formatted_prompt)

            raw = response.content.strip()
            if raw.startswith("```"):
                lines = [l for l in raw.split("\n") if not l.strip().startswith("```")]
                raw = "\n".join(lines).strip()

            parsed = json.loads(raw)

            if isinstance(parsed, dict):
                parsed = [parsed]

            tasks = [LibrarianTask(**t) for t in parsed]

            return {
                "messages": [AIMessage(content=response.content)],
                "action": tasks,
            }
        except Exception as e:
            print(f"[Librarian] Model node error: {type(e).__name__}: {e}")
            return {}

    #Librarian decision node routes to the tool execution node, hitl node, or final response node 
    # based on the current state of the agent.
    def librarian_decision_node(self, state: LibrarianState) -> dict:
        """
        Routes to hitl, tool_node, or final_response based on current state.
        """
        if state.hitl_state:
            next_step = "hitl"
        elif any(task.status == "pending" for task in state.action):
            next_step = "tool_node"
        else:
            next_step = "final_response"
        return {"next_step": next_step}

    #Librarian tool execution node executes the next pending task using the appropriate tool. 
    # For update_policy tasks, it pushes the task to hitl_state so the decision node can route to the HITL node before carrying out the update.
    def librarian_tool_execution_node(self, state: LibrarianState) -> dict:
        """
        Executes the next pending LibrarianTask using the appropriate tool.
        For update_policy the task is pushed to hitl_state so the decision
        node can route to the HITL node before the update is carried out.
        """
        try:
            updated_actions = [task.model_copy() for task in state.action]
            pending_task = next((t for t in updated_actions if t.status == "pending"), None)

            if not pending_task:
                return {}

            if pending_task.action == "update_policy":
                if pending_task.hitl_response is None:
                    pending_task.status = "waiting_for_human"
                    
                    updated_hitl = list(state.hitl_state) + [pending_task]
                    return {
                        "messages": [AIMessage(
                            content="This task requires human confirmation before updating the policy document."
                        )],
                        "action": updated_actions,
                        "hitl_state": updated_hitl,
                    }

                
                if pending_task.hitl_response is True:
                    
                    document_content = state.user_query.UploadedText or pending_task.query
                    update_result = self.update_tool.invoke({"document_content": document_content})
                    pending_task.result = (
                        "Policy document updated successfully."
                        if update_result
                        else "Failed to update the policy document."
                    )
                else:
                    pending_task.result = "Policy update cancelled by the user."

                pending_task.status = "completed"

            elif pending_task.action == "delete_policy":
                
                pending_task.result = (
                    "To remove a policy, please upload an updated version of the document "
                    "with the necessary changes. This preserves a full audit trail."
                )
                pending_task.status = "completed"

            elif pending_task.action == "retrieve_policy": 
                retrieval_results = self.retrieval_tool.invoke({"query": pending_task.query})
                pending_task.result = f"Retrieved the following documents based on the query: {retrieval_results}"
                pending_task.status = "completed"

            elif pending_task.action == "upload_policy":   
                document_content = state.user_query.UploadedText or pending_task.query
                insertion_result = self.insertion_tool.invoke({"document_content": document_content})
                pending_task.result = "Policy uploaded successfully." if insertion_result else "Policy upload failed."
                pending_task.status = "completed"

            return {
                "messages": [AIMessage(content=pending_task.result)],
                "action": updated_actions,
            }

        except Exception as e:
            print(f"[Librarian] Tool execution error: {type(e).__name__}: {e}")
            return {
                "messages": [AIMessage(
                    content=f"Error executing the task using the tool. Please try again later. {e}"
                )]
            }

    # HITL node broadcasts the HITL task details to the frontend, 
    # waits for the user's response on a Redis pub/sub channel,
    # then updates the agent's state with the response to resume task execution.
    async def librarian_hitl_node(self, state: LibrarianState) -> dict:
        """
        Broadcasts a HITL event over WebSocket, then waits on the async
        Redis pub/sub channel for the user's approval or rejection before
        returning control to the tool execution node.
        """
        user_id = state.user_query.user_id
        conversation_id = state.user_query.conversation_id

        hitl_state_list = list(state.hitl_state)
        hitl_task: LibrarianTask = hitl_state_list.pop(0)

        event_payload = {
            "user_id": user_id,
            "conversation_id": conversation_id,
            "agent": "Librarian",
            "hitl_task": hitl_task.model_dump(),
        }

        save_agent_state_for_hitl_intervention(
            AgentState(
                user_id=user_id,
                key=conversation_id,
                agent_name="Librarian",
                state={"hitl_task": hitl_task.model_dump()},
            )
        )

        await broadcast_hitl_event(
            user_id=user_id,
            conversation_id=conversation_id,
            agent_name="Librarian",
            event_data=event_payload,
        )


        redis = get_async_redis_client()
        pubsub = redis.pubsub()
        response_channel = f"HITL_Response_Channel:{user_id}:{conversation_id}:Librarian"
        await pubsub.subscribe(response_channel)

        result: dict = {}
        try:
            async for message in pubsub.listen():
                if message["type"] == "message":
                    response_payload = json.loads(message["data"])

                    await pubsub.unsubscribe(response_channel)

                    updated_actions = [task.model_copy() for task in state.action]
                    pending_task = next(
                        (t for t in updated_actions if t.status == "waiting_for_human"), None
                    )

                    if not pending_task:
                        result = {
                            "hitl_state": hitl_state_list,
                            "messages": [AIMessage(content="HITL error: no waiting task found.")],
                        }
                    else:
                        raw_response = response_payload.get("detail", response_payload.get("approved", None))
                        if isinstance(raw_response, str):
                            pending_task.hitl_response = raw_response.strip().lower() in ("approve", "approved", "true", "yes")
                        elif isinstance(raw_response, bool):
                            pending_task.hitl_response = raw_response
                        else:
                            pending_task.hitl_response = False

                        pending_task.status = "pending"
                        result = {
                            "action": updated_actions,
                            "hitl_state": hitl_state_list,
                            "messages": [AIMessage(
                                content=f"Received user response for HITL task: {pending_task.hitl_response}. "
                                        "Re-evaluating the task based on the user's response."
                            )],
                        }
                    break
        finally:
            await pubsub.aclose()
            await redis.aclose()

        return result

    # The final response node generates the final response to the user after all tasks have been executed.
    def librarian_final_response_node(self, state: LibrarianState) -> dict:
        """
        Generates the final user-facing response after all tasks are complete.
        """
        formatted_prompt = LibrarianFinalResponsePrompt.format_messages(
            user_query=state.user_query.query,
            tasks=list(state.action),
        )
        counter = 3
        while counter > 0:
            try:
                response = self.llm_model.invoke(list(state.messages) + formatted_prompt)

                user_id = state.user_query.user_id
                conversation_id = state.user_query.conversation_id

                existing = get_agent_state_for_final_response(user_id, conversation_id, "Librarian")
                agent_state = AgentState(
                    user_id=user_id,
                    key=conversation_id,
                    agent_name="Librarian",
                    state={
                        **(existing or {}),
                        "status": "completed",
                        "final_response": response.content,
                    },
                )
                save_agent_state_for_final_response(agent_state)

                return {
                    "messages": [AIMessage(content=response.content)],
                    "response": response.content,
                }
            except Exception as e:
                print(f"[Librarian] Final response error: {type(e).__name__}: {e}. Retrying…")
                counter -= 1

        print("[Librarian] Failed to generate final response after multiple attempts.")
        return {
            "messages": [AIMessage(content="Sorry, I am unable to generate a response at the moment.")],
        }

    
    def create_librarian_agent_graph(self) -> StateGraph:
        """
        Builds and compiles the Librarian Agent state graph.
        """
        librarian_graph = StateGraph(LibrarianState)
        librarian_graph.add_node("model_node", self.librarian_model_node)
        librarian_graph.add_node("decision_node", self.librarian_decision_node)
        librarian_graph.add_node("tool_node", self.librarian_tool_execution_node)
        librarian_graph.add_node("hitl_node", self.librarian_hitl_node)
        librarian_graph.add_node("final_response", self.librarian_final_response_node)

        librarian_graph.add_edge(START, "model_node")
        librarian_graph.add_edge("model_node", "decision_node")
        librarian_graph.add_conditional_edges(
            "decision_node",
            lambda state: state.next_step,
            {
                "tool_node": "tool_node",
                "hitl": "hitl_node",
                "final_response": "final_response",
            },
        )
        librarian_graph.add_edge("tool_node", "decision_node")
        librarian_graph.add_edge("hitl_node", "tool_node")
        librarian_graph.add_edge("final_response", END)
        return librarian_graph.compile()

    def display_librarian_agent_graph(self, agent: StateGraph):
        png_bytes = agent.get_graph(xray=True).draw_mermaid_png()
        with open("librarian_agent_graph.png", "wb") as f:
            f.write(png_bytes)
        display(Image(png_bytes))