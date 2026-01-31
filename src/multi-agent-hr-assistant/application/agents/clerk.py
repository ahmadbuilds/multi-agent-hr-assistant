from infrastructure.llm_providers.ollama_provider import create_model_instance
from domain.ports import LeaveBalancePort
from infrastructure.adapters.clerk_leave_balance_adapter import ClerkLeaveBalanceAdapter
from domain.tools.clerk_tool import make_get_leave_balance_tool
from domain.prompts.clerk_prompt import Clerk_Classification_prompt,Clerk_Inner_Model_Prompt
from domain.entities import ClerkMultipleTasksOutput
from states import ClerkClassificationState, ClerkState
from langchain.chat_models import BaseChatModel
from langgraph.graph import END
from typing import Literal
from collections import deque
from langchain_core.messages import AIMessage

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
    def Clerk_Decision_Node(state:ClerkState)->Literal["clerk_inner_model_node","final_response_node"]:
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
        current_task=state.pending_tasks.popleft()
        formatted_prompt=Clerk_Inner_Model_Prompt.format_messages(
                current_task=current_task,
                user_query=state.user_query.query
            )
        structured_llm_model=self.llm_model.with_structured_output(ClerkClassificationState)
        response=structured_llm_model.invoke([formatted_prompt]+state.messages)
        
        if current_task.action=="general_information" or current_task.action=="get_balance":
            state.final_response.append(current_task)
            return{
                "messages":state.messages+[AIMessage(content=response.model_dump_json())],
                "final_response":state.final_response
            }

    #Clerk Tool Execution Node
    def Clerk_Tool_Execution_Node(self, state:ClerkState)->dict:
        """
        Tool Execution Node for Clerk Agent to execute tools based on the action type.
        """
        tool_execution=state.final_response[-1]
        if tool_execution.action=="get_balance":
            get_balance_tool=make_get_leave_balance_tool(self.leave_balance_port)
            balance=get_balance_tool.run(user_query=state.user_query.query)
            state.tool_results.append({"leave_balance":balance})
            return{
                "tool_results":state.tool_results
            }