from typing import Literal

from langgraph.graph import StateGraph,START,END
from domain.prompts.supervisor_prompt import SupervisorPrompt
from domain.tools.supervisor_tool import make_supervisor_execute_clerk_graph_tool
from infrastructure.adapters.supervisor_clerk_graph_executor import SupervisorClerkGraphExecutor
from application.states import SupervisorState,ClerkState
from langchain.chat_models import BaseChatModel
from infrastructure.redis.redis_client import get_agent_state_for_final_response
from domain.entities import TaskIntent
from langchain_core.messages import AIMessage
#Supervisor Agent State Graph
class SupervisorAgent:
    def __init__(self,llm_model:BaseChatModel,SupervisorClerkGraphExecutorPort:SupervisorClerkGraphExecutor):
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
            formatted_prompt=SupervisorPrompt.format_messages(
                user_query=state.user_query.query,
                isUploaded=state.user_query.UploadedText,
                isAdmin=state.user_query.isAdmin
            )
            structured_llm_prompt=self.llm_model.with_structured_output(TaskIntent)
            response= structured_llm_prompt.invoke([formatted_prompt]+state.messages)
            state.identified_intent=response
            state.decision_node_count=len(response) if isinstance(response, list) else 0
            return{
                "messages":state.messages+[AIMessage(content=response.model_dump_json())],
                "identified_intent":state.identified_intent
            }
        except Exception as e:
            print(f"Error in decompose_query_into_tasks: {e}")
            return {
                "messages":state.messages,
                "identified_intent":[]
            }
    
    #function to decide the next action based on the identified intents and execute the corresponding tools or agent graphs
    def Supervisor_decision_node(self,state:SupervisorState)->Literal["result_node","supervisor_tool_node"]:
        """
        function to decide the next action based on the identified intents and decision node count, and execute the corresponding tools or agent graphs
        """
        if state.decision_node_count==0:
            return "result_node"
        else:
            return "supervisor_tool_node"
        
    