from typing import Literal
from langgraph.graph import StateGraph,START,END
from domain.prompts.supervisor_prompt import SupervisorDecompositionPrompt,SupervisorFinalResponsePrompt
from domain.tools.supervisor_tool import make_supervisor_execute_clerk_graph_tool
from application.states import SupervisorState,ClerkState
from langchain.chat_models import BaseChatModel
from infrastructure.redis.redis_client import get_agent_state_for_final_response
from domain.entities import SupervisorTaskIntent
from langchain_core.messages import AIMessage, HumanMessage
from domain.ports import ClerkGraphExecutionPort
from IPython.display import Image,display
#Supervisor Agent State Graph
class SupervisorAgent:
    def __init__(self,llm_model:BaseChatModel,SupervisorClerkGraphExecutorPort:ClerkGraphExecutionPort):
        self.llm_model=llm_model
        self.SupervisorClerkGraphExecutorPort=SupervisorClerkGraphExecutorPort

    #function to decompose the user query into multiple tasks if multiple intents are identified
    def decompose_query_into_tasks(self,state:SupervisorState)->dict:
        """
        Function to decompose the user query into multiple tasks if multiple intents are identified
        Args:
            state (SupervisorState): Current state of the Supervisor Agent
        returns:
            SupervisorState: Updated state with decomposed tasks
        """
        try:
            formatted_prompt=SupervisorDecompositionPrompt.format_messages(
                user_query=state.user_query.query,
                isUploaded=state.user_query.UploadedText,
                isAdmin=state.user_query.isAdmin
            )
            structured_llm_prompt=self.llm_model.with_structured_output(SupervisorTaskIntent)
            response= structured_llm_prompt.invoke(list(state.messages)+formatted_prompt)

            tasks=response.task
            
            return{
                "messages":[AIMessage(content=response.model_dump_json())],
                "identified_intent":tasks
            }
        except Exception as e:
            print(f"Error in decompose_query_into_tasks: {e}")
            return {
                "identified_intent":[]
            }
    
    #function to decide the next action based on the identified intents and execute the corresponding tools or agent graphs
    def Supervisor_decision_node(self,state:SupervisorState)->Literal["result","tool_node"]:
        """
        function to decide the next action based on the identified intents and decision node count, and execute the corresponding tools or agent graphs
        args:
            state (SupervisorState): Current state of the Supervisor Agent
        returns:
            str: "result" if all tasks are completed or in error state, "tool_node" if there are still pending tasks to be executed
        """
        pending_tasks=[intent for intent in state.identified_intent if intent.status=="pending"]
        
        if not pending_tasks:
            state.next_steps="result"
        else:
            state.next_steps="tool_node"
        
        return state.next_steps
    #function to Supervisor Tool Node which executes the corresponding agent graph or tool based on the identified intents
    def Supervisor_tool_node(self,state:SupervisorState)->dict:
        """
        function to Supervisor Tool Node which executes the corresponding agent graph or tool based on the identified intents
        """
        pending_tasks=[intent for intent in state.identified_intent if intent.status=="pending"] 

        if not pending_tasks:
            return {}

        tasks=pending_tasks[0]
        tasks.status="running"
        try:
            if tasks.agent.lower()=="supervisor":
                #if the agent is supervisor than it is a general query which does not require any tool execution or agent graph execution, so we can skip it for now
                state.active_agent="Supervisor"
                tasks.status="running"
                response=self.llm_model.invoke(state.messages+[HumanMessage(content=tasks.decomposed_query)])
                
                tasks.status="completed"
                tasks.result=response.content
            
            elif tasks.agent.lower()=="clerk":
                #if the agent is clerk than we need to execute the corresponding agent graph for the clerk agent
                
                state.active_agent="Clerk"
                
                tasks.status="running"
                updated_query=state.user_query.copy(update={"query":tasks.decomposed_query})
                clerk_state=ClerkState(
                    user_query=updated_query,
                )

                #invoking the Clerk Agent Graph Executor Port to execute the Clerk Agent Graph with the updated clerk state
                self.SupervisorClerkGraphExecutorPort.update_clerk_state(clerk_state)
                clerk_graph_executor=make_supervisor_execute_clerk_graph_tool(self.SupervisorClerkGraphExecutorPort)
                clerk_graph_executor(clerk_state)

                #reading the final response of the clerk agent from Redis after execution
                final_clerk_response=get_agent_state_for_final_response(state.user_query.user_id,state.user_query.conversation_id)
                tasks.status="completed"
                tasks.result=final_clerk_response

        except Exception as e:
            print(f"Error in Supervisor_tool_node for intent {tasks.intent}: {e}")
            tasks.status="error"
            tasks.result=str(e)
        

        return{
            "identified_intent":state.identified_intent,
        }
    
    #function to generate the final response for the user after executing all the tools and agent graphs based on the identified intents
    def Supervisor_result_node(self,state:SupervisorState)->dict:
        """
        function to generate the final response for the user after executing all the tools and agent graphs based on the identified intents
        args:
            state (SupervisorState): Current state of the Supervisor Agent
        returns:
            dict: Dictionary containing the final response to be sent to the user
        """
        try:
            formatted_prompt=SupervisorFinalResponsePrompt.format_messages(
                user_query=state.user_query.query,
                identified_intent=state.identified_intent   
            )

            response=self.llm_model.invoke(list(state.messages)+formatted_prompt)
            return {
                "messages":[AIMessage(content=response.content)],
                "final_response":response.content
            }
        except Exception as e:
            print(f"Error in Supervisor_result_node: {e}")
            return {
                "messages":[AIMessage(content="Sorry, I am having trouble generating the final response at the moment.")],
                "final_response":"Sorry, I am having trouble generating the final response at the moment."
            }
        
    #function to create the Supervisor Agent State Graph
    def create_supervisor_agent_graph(self)->StateGraph:
        """
        function to create the Supervisor Agent State Graph with the defined nodes and transitions
        args:
            None
        returns:
            StateGraph: StateGraph object representing the Supervisor Agent State Graph
        """
        graph=StateGraph(SupervisorState)
        graph.add_node("decompose_query_into_tasks",self.decompose_query_into_tasks)
        graph.add_node("Supervisor_decision_node",self.Supervisor_decision_node)
        graph.add_node("Supervisor_tool_node",self.Supervisor_tool_node)
        graph.add_node("Supervisor_result_node",self.Supervisor_result_node)
        graph.add_edge(START,"decompose_query_into_tasks")
        graph.add_edge("decompose_query_into_tasks","Supervisor_decision_node")
        graph.add_conditional_edges(
            "Supervisor_decision_node",
            lambda state:state.next_steps,{
                "result":"Supervisor_result_node",
                "tool_node":"Supervisor_tool_node"
            }
        )
        graph.add_edge("Supervisor_tool_node","Supervisor_decision_node")
        graph.add_edge("Supervisor_result_node",END)
        return graph.compile()
    
    #function to build the image for the Supervisor Agent Graph
    def build_supervisor_agent_graph_image(self,agent:StateGraph):
        """
        function to build the image for the Supervisor Agent Graph
        args:
            agent (StateGraph): StateGraph object representing the Supervisor Agent State Graph
        returns:
            bytes: Byte content of the generated image for the Supervisor Agent Graph
        """
        png_bytes =agent.get_graph(xray=True).draw_mermaid_png()

         # Save to file
        with open("supervisor_agent_graph.png", "wb") as f:
            f.write(png_bytes)

        display(Image(png_bytes))