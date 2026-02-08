from domain.ports import ClerkGraphExecutionPort
from langchain.tools import tool

#Wrapper function to execute the Clerk Agent State Graph
def make_supervisor_execute_clerk_graph_tool(executor:ClerkGraphExecutionPort):
    @tool(
        name="execute_clerk_graph",
        description="Use this tool to execute the Clerk Agent State Graph for handling HR related queries."
    )
    def execute_clerk_graph()->None:
        """
        Tool function to execute the Clerk Agent State Graph
        Args:
            state (ClerkState): Current state of the Clerk Agent
        Returns:
            None
        """
        return executor.execute_clerk_agent_graph()