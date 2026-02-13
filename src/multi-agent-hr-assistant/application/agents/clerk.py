from domain.ports import LeaveBalancePort,TicketCreationPort
from domain.tools.clerk_tool import make_get_leave_balance_tool,make_ticket_creation_tool
from domain.prompts.clerk_prompt import Clerk_Classification_prompt,Clerk_Inner_Model_Prompt,Clerk_Final_Response_Prompt
from domain.entities import ClerkMultipleTasksOutput, TicketCreation
from application.states import ClerkClassificationState, ClerkState
from langchain.chat_models import BaseChatModel
from langgraph.graph import END,StateGraph,START
from typing import Literal
from collections import deque
from langchain_core.messages import AIMessage
from IPython.display import Image,display
from infrastructure.redis.redis_client import save_agent_state_for_final_response,get_agent_state_for_final_response,publish_event,save_agent_state_for_hitl_intervention
from infrastructure.redis.redis_config import get_redis_client
import json
#Clerk Agent Class Implementation
class ClerkAgent:
    def __init__(self, llm_model:BaseChatModel, leave_balance_port:LeaveBalancePort,ticket_creation_port:TicketCreationPort):
        self.llm_model=llm_model
        self.leave_balance_port=leave_balance_port
        self.ticket_creation_port=ticket_creation_port

    #Model Node for Clerk Agent
    def Clerk_Outer_Model_Node(self, state:ClerkState)->dict:
        """
        function to invoke the Clerk Outer Model Node for classifying tasks into Multiple Intents
        based on the user query present in the Clerk State.
        """
        try:
            formatted_prompt=Clerk_Classification_prompt.format_messages(query=state.user_query.query)
            structured_llm_model=self.llm_model.with_structured_output(ClerkMultipleTasksOutput)
            response=structured_llm_model.invoke([formatted_prompt]+state.messages)
            return {
                "messages":state.messages+[AIMessage(content=response.model_dump_json())],
                "pending_tasks":deque(response.tasks)
            }
        except Exception as e:
            print(f"Exception in Clerk Outer Model Node: {e}")
            return {
                "messages":state.messages,
                "pending_tasks":deque()
            }
    #Decision Node for Clerk Agent
    def Clerk_Decision_Node(self,state:ClerkState)->Literal["inner","final","hitl"]:
        """
        Decision Node for Clerk Agent to decide whether to proceed to Inner Model Node
        or to Final Response Node based on the pending tasks in the Clerk State.
        """
        if state.hitl_state:
            state.next_step="hitl"
        elif state.pending_tasks:
            state.next_step="inner"
        else:
            state.next_step="final"

        return state.next_step
    #Clerk Inner Model Node
    def Clerk_Inner_Model_Node(self, state:ClerkState)->dict:
        """
        Inner Model Node for Clerk Agent to handle individual tasks based on the action type.
        """
        try:
            current_task=state.pending_tasks.popleft()
            formatted_prompt=Clerk_Inner_Model_Prompt.format_messages(
                    current_task=current_task,
                    user_query=state.user_query.query
                )
            structured_llm_model=self.llm_model.with_structured_output(ClerkClassificationState)
            response=structured_llm_model.invoke([formatted_prompt]+state.messages)
            
            if current_task.action=="general_information" or current_task.action=="get_balance" or current_task.action=="ticket_creation":
                state.final_response.append(response)
                return{
                    "messages":state.messages+[AIMessage(content=response.model_dump_json())],
                    "final_response":state.final_response,
                    "pending_tasks":state.pending_tasks
                }

        except Exception as e:
            print(f"Exception in Clerk Inner Model Node: {e}")
            return {
                "messages":state.messages,
                "final_response":state.final_response,
                "pending_tasks":state.pending_tasks
            }
    #Clerk Tool Execution Node
    def Clerk_Tool_Execution_Node(self, state:ClerkState)->dict:
        """
        Tool Execution Node for Clerk Agent to execute tools based on the action type.
        """
        if not state.final_response:
            return {}
        tool_execution:ClerkClassificationState = state.final_response[-1]
        if tool_execution.action=="get_balance":
            already_executed=any(
                result.get("action")=="get_balance" for result in state.tool_results
            )

            if not already_executed:
                counter=3
                while counter>0:
                    try:
                        leave_balance_tool=make_get_leave_balance_tool(self.leave_balance_port,state.user_query.auth_token)
                        leave_balance:int=leave_balance_tool()
                        state.tool_results.append({
                            "action":"get_balance",
                            "success":True,
                            "data":{"leave_balance":leave_balance},
                            "error":None,
                        })
                        break
                    except Exception as e:
                        print("Error executing get_balance tool:Retrying...", str(e))
                        counter-=1
                        if counter==0:
                            print("Failed to execute get_balance tool after multiple attempts.")
                            state.tool_results.append({
                                "action":"get_balance",
                                "success":False,
                                "data":None,
                                "error":str(e),
                            })
        elif tool_execution.action=="ticket_creation":
            counter=3
            while counter>0:
                try:
                    #Checking if LLM has extracted the necessary details for ticket creation or not
                    if not all([tool_execution.details.get("ticket_type"), tool_execution.details.get("subject"), tool_execution.details.get("description")]):
                        state.hitl_state.append(tool_execution)
                        return {
                            "hitl_state":state.hitl_state,
                            "messages":state.messages+[AIMessage(content="Insufficient details for ticket creation. Need HITL intervention.")],
                        }
                    elif tool_execution.details.get("ticket_type")=="leave" and tool_execution.details.get("leave_days") is None:
                        state.hitl_state.append(tool_execution)
                        return{
                            "hitl_state":state.hitl_state,
                            "messages":state.messages+[AIMessage(content="Insufficient details for leave ticket creation. Need HITL intervention.")],
                        }
                    elif tool_execution.details.get("ticket_type")=="complaint" or tool_execution.details.get("ticket_type")=="leave":
                        state.hitl_state.append(tool_execution)
                        return{
                            "hitl_state":state.hitl_state,
                            "messages":state.messages+[AIMessage(content="Need Confirmation from user for creating a complaint or leave ticket. Need HITL intervention.")],
                        }
                    
                    #proceeding with ticket creation if all necessary details are present
                    ticket_creation_date=TicketCreation(
                        ticket_type=tool_execution.details.get("ticket_type"),
                        subject=tool_execution.details.get("subject"),
                        description=tool_execution.details.get("description"),
                        status="in_progress",
                        leave_days=tool_execution.details.get("leave_days"),
                        accepted=tool_execution.details.get("accepted")
                    )
                    ticket_creation_tool=make_ticket_creation_tool(self.ticket_creation_port,ticket_creation_date,state.user_query.auth_token)
                    response:bool=ticket_creation_tool()
                    state.tool_results.append({
                        "action":"ticket_creation",
                        "success":response,
                        "data":tool_execution.details if response else None,
                        "error":None if response else "Ticket creation failed due to unknown error.",
                    })
                    break
                except Exception as e:
                    print(f"Error validation and creating Ticket for the user", str(e))
                    counter-=1
                    if counter==0:
                        print("Failed to validate and create ticket after multiple attempts.")
                        state.tool_results.append({
                            "action":"ticket_creation",
                            "success":False,
                            "data":None,
                            "error":str(e),
                        })
        return {
            "tool_results":state.tool_results,
        }

    #Clerk HITL Intervention Node
    def hitl_intervention_node(self,state:ClerkState)->dict:
        """
        HITL Intervention Node for Clerk Agent to handle tasks that require human intervention based on the hitl_state in the Clerk State.
        """
        #publishing event to Redis channel for HITL intervention
        user_id=state.user_query.user_id
        conversation_id=state.user_query.conversation_id

        hitl_data=state.hitl_state.popleft()
        publish_event(
            channel=f"HITL_Intervention_Channel:{user_id}:{conversation_id}:Clerk",
            event_data={
                "user_id":user_id,
                "conversation_id":conversation_id,
                "agent":"Clerk",
                "hitl_task":hitl_data.model_dump()
            }
        )

        #saving the updated Clerk State with HITL state to Redis
        save_agent_state_for_hitl_intervention(state)
        
        redis=get_redis_client()

        pubsub=redis.pubsub()

        pubsub.subscribe(f"HITL_Response_Channel:{user_id}:{conversation_id}:Clerk")

        for message in pubsub.listen():
            if message["type"]=="message":
                response_payload=json.loads(message["data"])

                pubsub.unsubscribe(f"HITL_Response_Channel:{user_id}:{conversation_id}:Clerk")

                result:ClerkClassificationState=state.final_response.popleft()
                result.details=response_payload.get("details",result.details)
                state.final_response.appendleft(result)
                return{
                    "final_response":state.final_response,
                    "messages":state.messages+[AIMessage(content="Received HITL response, resuming task execution.")],
                }
    

    #Final Response Node for Clerk Agent
    def Clerk_Final_Response_Node(self,state:ClerkState)->END:
        """
        final response node for Clerk Agent to compile final responses based on the tool results and final responses.
        """ 
        formatted_prompt=Clerk_Final_Response_Prompt.format_messages(
                final_response=list(state.final_response),
                tool_results=state.tool_results
            )      
        counter=3
        while counter>0:
            try:
                response=self.llm_model.invoke([formatted_prompt]+state.messages)
                user_id=state.user_query.user_id
                conversation_id=state.user_query.conversation_id
                #updating the final response in Redis after successful execution
                agent_state=get_agent_state_for_final_response(user_id,conversation_id)
                if agent_state:
                    agent_state["final_response"]=response
                    save_agent_state_for_final_response(agent_state)
                return END
            except Exception as e:
                print(f"Exception in Clerk Final Response Node: {e}. Retrying...")
                counter-=1
    
    #Function to create the Clerk Agent State Graph
    def create_clerk_agent_graph(self)->StateGraph:
        clerk_graph=StateGraph(ClerkState)
        
        #adding nodes to the clerk agent graph
        clerk_graph.add_node("clerk_outer_model_node", self.Clerk_Outer_Model_Node)
        clerk_graph.add_node("clerk_decision_node", self.Clerk_Decision_Node)
        clerk_graph.add_node("clerk_inner_model_node", self.Clerk_Inner_Model_Node)
        clerk_graph.add_node("clerk_tool_execution_node", self.Clerk_Tool_Execution_Node)
        clerk_graph.add_node("final_response_node", self.Clerk_Final_Response_Node)
        clerk_graph.add_node("hitl_intervention_node", self.hitl_intervention_node)
        #defining edges between nodes
        clerk_graph.add_edge(START, "clerk_outer_model_node")
        clerk_graph.add_edge("clerk_outer_model_node", "clerk_decision_node")
        clerk_graph.add_conditional_edges(
            "clerk_decision_node",
            lambda state:state.next_step,
            {
                "inner":"clerk_inner_model_node",
                "final":"final_response_node",
                "hitl":"hitl_intervention_node"
            }
        )
        clerk_graph.add_edge("clerk_inner_model_node", "clerk_tool_execution_node")
        clerk_graph.add_edge("clerk_tool_execution_node", "clerk_decision_node")
        clerk_graph.add_edge("final_response_node", END)
        clerk_graph.add_edge("hitl_intervention_node", "clerk_tool_execution_node")
        
        #Compiling the Graph
        clerk_agent=clerk_graph.compile()
        
        return clerk_agent

    #function to display the clerk agent graph
    def display_clerk_agent_graph(self,agent:StateGraph):
        png_bytes =agent.get_graph(xray=True).draw_mermaid_png()

         # Save to file
        with open("clerk_agent_graph.png", "wb") as f:
            f.write(png_bytes)

        display(Image(png_bytes))