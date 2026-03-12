from langchain_core.messages import BaseMessage,HumanMessage,AIMessage
from domain.ports import LibrarianRetrievalPort, LibrarianInsertionPort, LibrarianUpdatePort
from domain.entities import LibrarianTaskIntent
from application.states import LibrarianState
from domain.tools.librarian_tool import make_librarian_retrieval_tool, make_librarian_insertion_tool, make_librarian_update_tool
from langchain_core.language_models.chat_models import BaseChatModel
try:
    from IPython.display import Image,display
except ImportError:
    Image=None
    display=None
from langgraph.graph import START,END,StateGraph
from domain.prompts.librarian_prompt import librarianPrompt,LibrarianFinalResponsePrompt
from typing import Literal
from infrastructure.redis.redis_client import publish_event, save_agent_state_for_final_response,get_agent_state_for_final_response,save_agent_state_for_hitl_intervention
from domain.entities import AgentState
import json
from infrastructure.redis.redis_config import get_redis_client
class LibrarianAgent:
    def __init__(self,llm_model:BaseChatModel,retrieval_port:LibrarianRetrievalPort,insertion_port:LibrarianInsertionPort,update_port:LibrarianUpdatePort):
        self.llm_model = llm_model
        self.retrieval_tool = make_librarian_retrieval_tool(retrieval_port)
        self.insertion_tool = make_librarian_insertion_tool(insertion_port)
        self.update_tool = make_librarian_update_tool(update_port)

    def librarian_model_node(self,state:LibrarianState)->dict:
        """
        method for classifying task into multiple intent based on the user query present in the librarian state
        Args:
            state (LibrarianState): Current state of the Librarian Agent
        Returns:
            dict: Updated state of the Librarian Agent after processing the model node
        """
        try:
            formatted_prompt=librarianPrompt.format_messages(
                user_query=state.user_query.query,
                isAdmin=state.user_query.isAdmin,
                UploadedText=state.user_query.UploadedText,
            )
            structured_llm_response=self.llm_model.with_structured_output(LibrarianTaskIntent)
            response=structured_llm_response.invoke(formatted_prompt+list(state.messages))
            return{
                "messages":[AIMessage(content=response.model_dump_json())],
                "action":response.task
            }
        except Exception as e:
            print("Error in Librarian Model Node:", str(e))
            return {}

    def librarian_decision_node(self,state:LibrarianState)->Literal["tool_node","final_response","hitl"]:
        """
        method for deciding the next step for the Librarian Agent based on the identified intent
        Args:
            state (LibrarianState): Current state of the Librarian Agent
        Returns:
            Literal["tool_node","final_response","hitl"]: Next step for the Librarian Agent to take, can be "tool_node" if there are pending tasks to be performed, "hitl" if there are tasks requiring human intervention and "final_response" if there are no pending tasks and no tasks requiring human intervention
        """
        if state.hitl_state:
            state.next_step="hitl"
        elif any(task.status=="pending" for task in state.action):
            state.next_step="tool_node"
        else:
            state.next_step="final_response"
        return state.next_step
    
    def librarian_tool_execution_node(self,state:LibrarianState)->dict:
        """
        method for executing the identified tasks using the appropriate tools and updating the state of the Librarian Agent based on the results of the tool execution
        Args:
            state (LibrarianState): Current state of the Librarian Agent
        Returns:
            dict: Updated state of the Librarian Agent after executing the identified tasks using the appropriate tools and updating the state of the Librarian Agent based on the results of the tool execution
        """
        try:
            updated_actions = [task.model_copy() for task in state.action]
            pending_task = next((t for t in updated_actions if t.status == "pending"), None)
            
            if not pending_task:
                return {}
            
            if pending_task.action=="update_document":
                if pending_task.hitl_response is None:
                    pending_task.result="This task requires human intervention. Please confirm if you want to proceed with updating the document based on the provided query."
                    pending_task.status="waiting_for_human"
                    return{
                        "messages":[AIMessage(content=pending_task.result)],
                        "action":updated_actions
                    }
                
                if pending_task.hitl_response:
                    update_result=self.update_tool.invoke({"document_content": pending_task.query})
                    if update_result:
                        pending_task.result="Document updated successfully."
                    else:
                        pending_task.result="Failed to update the document."
                else:
                    pending_task.result="Document update cancelled by the user."
                
                pending_task.status="completed"

            elif pending_task.action=="delete_policy":
                #simply tell user to use the update method instead of deleting 
                pending_task.result="To delete a policy, please update the policy document with the necessary changes instead of deleting it entirely. This way we can maintain a record of all policies and their updates."
                pending_task.status="completed"
                
            elif pending_task.action=="retrieve_document":
                retrieval_results=self.retrieval_tool.invoke({"query": pending_task.query})
                pending_task.result=f"Retrieved the following documents based on the query: {retrieval_results}"
                pending_task.status="completed"
                
            elif pending_task.action=="insert_document":
                insertion_result = self.insertion_tool.invoke({"document_content": pending_task.query})
                pending_task.result = "Inserted successfully." if insertion_result else "Insertion failed."
                pending_task.status = "completed"
            

            return{
                "messages":[AIMessage(content=pending_task.result)],
                "action":updated_actions
            }
        except Exception as e:
            print("Error in Librarian Tool Execution Node:", str(e))
            return {"messages":[AIMessage(content="Error executing the task using the tool. Please try again later."+str(e))]}


    def librarian_hitl_node(self,state:LibrarianState)->dict:
        """
        method for handling human intervention for tasks that require human intervention in the Librarian Agent and updating the state of the Librarian Agent based on the user's response for the HITL task
        args:
            state (LibrarianState): Current state of the Librarian Agent
        returns:
            dict: Updated state of the Librarian Agent after handling human intervention for tasks that require human intervention and updating the state of the Librarian Agent based on the user's response for the HITL task
        """
        try:
            user_id=state.user_query.user_id
            conversation_id=state.user_query.conversation_id

            hitl_task=state.hitl_state.pop()

            publish_event(channel=f"HITL_Intervention_Channel:{user_id}:{conversation_id}:Librarian", event_data={
                "user_id": user_id,
                "conversation_id": conversation_id,
                "agent":"Librarian",
                "action": hitl_task.model_dump_json(),
            })

            #saving the librarian state to redis for retrieval when the user responds to the HITL prompt
            save_agent_state_for_hitl_intervention(AgentState(
                user_id=user_id,
                key=conversation_id,
                agent_name="Librarian",
                state={"hitl_task":hitl_task.model_dump()}
            ))

            redis=get_redis_client()
            pubsub = redis.pubsub()

            pubsub.subscribe(f"HITL_Response_Channel:{user_id}:{conversation_id}:Librarian")

            for message in pubsub.listen():
                if message["type"] == "message":
                    response_payload = json.loads(message["data"])

                    pubsub.unsubscribe(f"HITL_Response_Channel:{user_id}:{conversation_id}:Librarian")

                    updated_actions = [task.model_copy() for task in state.action]
                    pending_task = next((t for t in updated_actions if t.status == "pending"), None)
            
                    if not pending_task:
                        return {}
                    pending_task.hitl_response = response_payload.get("detail",pending_task.hitl_response)
                    pending_task.status = "pending"  # Set back to pending for re-evaluation in the decision node
                    return{
                        "messages":[AIMessage(content=f"Received user response for HITL task: {pending_task.hitl_response}. Re-evaluating the task based on the user's response.")],
                        "action":updated_actions
                    }
        except Exception as e:
            print("Error in Librarian HITL Node:", str(e))
            return {"messages":[AIMessage(content="Error handling human intervention for the task. Please try again later."+str(e))]}
    
    #librarian final response node to generate the final response for the user after all tasks have been executed and there are no tasks requiring human intervention
    def librarian_final_response_node(self,state:LibrarianState)->dict:
        """
        method for generating the final response for the user after all tasks have been executed and there are no tasks requiring human intervention in the Librarian Agent
        args:
            state (LibrarianState): Current state of the Librarian Agent
        returns:
            dict: Updated state of the Librarian Agent after generating the final response for the user
        """
        formatted_prompt=LibrarianFinalResponsePrompt.format_messages(
            user_query=state.user_query.query,
            task_results=list(state.action),
        )
        counter=3
        while counter>0:
            try:
                response=self.llm_model.invoke(formatted_prompt+list(state.messages))
                user_id=state.user_query.user_id
                conversation_id=state.user_query.conversation_id

                existing=get_agent_state_for_final_response(user_id, conversation_id, "Librarian")
                agent_state=AgentState(
                    user_id=user_id,
                    key=conversation_id,
                    agent_name="Librarian",
                    state={
                        **existing,
                        "status":"completed",
                        "final_response":response.content,
                    }
                )
                save_agent_state_for_final_response(agent_state)
                return {
                    "messages":[AIMessage(content=response.content)],
                    "response":response.content,
                }
            except Exception as e:
                print("Error in Librarian Final Response Node:", str(e),"Retrying...")
                counter-=1
        print("Failed to generate final response after multiple attempts.")
        return {
            "messages":[AIMessage(content="Sorry, I am unable to generate a response at the moment.")],
        }

    #function to create the Librarian Agent State Graph
    def create_librarian_agent_graph(self)->StateGraph:
        """
        method for creating the state graph for the Librarian Agent
        args:
            None
        returns:
            StateGraph: State graph for the Librarian Agent containing the model node, decision node, tool execution node, HITL node and final response node
        """
        librarian_graph=StateGraph(LibrarianState)
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
                "final_response": "final_response"
            }    
        )
        librarian_graph.add_edge("tool_node", "decision_node")
        librarian_graph.add_edge("hitl_node", "tool_node")
        librarian_graph.add_edge("final_response", END)
        return librarian_graph.compile()
    #function to display the Librarian agent graph
    def display_librarian_agent_graph(self,agent:StateGraph):
        png_bytes =agent.get_graph(xray=True).draw_mermaid_png()

         # Save to file
        with open("librarian_agent_graph.png", "wb") as f:
            f.write(png_bytes)

        display(Image(png_bytes))