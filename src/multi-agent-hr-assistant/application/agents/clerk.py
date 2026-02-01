from domain.ports import LeaveBalancePort
from domain.tools.clerk_tool import make_get_leave_balance_tool
from domain.prompts.clerk_prompt import Clerk_Classification_prompt,Clerk_Inner_Model_Prompt,Clerk_Final_Response_Prompt
from domain.entities import ClerkMultipleTasksOutput
from application.states import ClerkClassificationState, ClerkState
from langchain.chat_models import BaseChatModel
from langgraph.graph import END,StateGraph,START
from typing import Literal
from collections import deque
from langchain_core.messages import AIMessage
from IPython.display import Image,display
#Clerk Agent Class Implementation
class ClerkAgent:
    def __init__(self, llm_model:BaseChatModel, leave_balance_port:LeaveBalancePort):
        self.llm_model=llm_model
        self.leave_balance_port=leave_balance_port

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
    def Clerk_Decision_Node(self,state:ClerkState)->Literal["clerk_inner_model_node","final_response_node"]:
        """
        Decision Node for Clerk Agent to decide whether to proceed to Inner Model Node
        or to Final Response Node based on the pending tasks in the Clerk State.
        """
        if state.pending_tasks:
            return "clerk_inner_model_node"
        else:
            return "final_response_node"
        
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
            
            if current_task.action=="general_information" or current_task.action=="get_balance":
                state.final_response.append(response)
                return{
                    "messages":state.messages+[AIMessage(content=response.model_dump_json())],
                    "final_response":state.final_response
                }
        except Exception as e:
            print(f"Exception in Clerk Inner Model Node: {e}")
            return {
                "messages":state.messages,
                "final_response":state.final_response
            }
    #Clerk Tool Execution Node
    def Clerk_Tool_Execution_Node(self, state:ClerkState)->dict:
        """
        Tool Execution Node for Clerk Agent to execute tools based on the action type.
        """
        tool_execution:ClerkClassificationState = state.final_response[-1]
        if tool_execution.action=="get_balance":
            already_executed=any(
                result.get("action")=="get_balance" for result in state.tool_results
            )

            if not already_executed:
                counter=3
                while counter>0:
                    try:
                        leave_balance_tool=make_get_leave_balance_tool(self.leave_balance_port)
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
        return {
            "tool_results":state.tool_results,
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

        #defining edges between nodes
        clerk_graph.add_edge(START, "clerk_outer_model_node")
        clerk_graph.add_edge("clerk_outer_model_node", "clerk_decision_node")
        clerk_graph.add_conditional_edges(
            "clerk_decision_node",
            lambda state:state.next_step,
            {
                "inner":"clerk_inner_model_node",
                "final":"final_response_node"
            }
        )
        clerk_graph.add_edge("clerk_inner_model_node", "clerk_tool_execution_node")
        clerk_graph.add_edge("clerk_tool_execution_node", "clerk_decision_node")
        clerk_graph.add_edge("final_response_node", END)
        
        #Compiling the Graph
        clerk_agent=clerk_graph.compile()
        
        return clerk_agent

    #function to display the clerk agent graph
    def display_clerk_agent_graph(self,agent:StateGraph):
        png_bytes =agent.get_graph(xray=True).draw_mermaid_png()

         # Save to file
        with open("clerk_agent_graph.png", "wb") as f:
            f.write(png_bytes)

        # Still display it in notebook
        display(Image(png_bytes))