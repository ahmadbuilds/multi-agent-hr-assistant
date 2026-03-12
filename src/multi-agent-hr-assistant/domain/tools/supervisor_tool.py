from domain.ports import ClerkGraphExecutionPort,LibrarianGraphExecutionPort
from langchain.tools import tool

#Wrapper function to execute the Clerk Agent State Graph
def make_supervisor_execute_clerk_graph_tool(executor:ClerkGraphExecutionPort):
    @tool(
        "execute_clerk_graph",
        description="Use this tool to execute the Clerk Agent State Graph for handling HR related queries."
    )
    def execute_clerk_graph()->bool:
        """
        Tool function to execute the Clerk Agent State Graph
        Args:
            state (ClerkState): Current state of the Clerk Agent
        Returns:
            bool: True if execution is successful, False otherwise
        """
        return executor.execute_clerk_agent_graph()
    return execute_clerk_graph

#wrapper function to execute the Librarian Agent State Graph
def make_supervisor_execute_librarian_graph_tool(executor:LibrarianGraphExecutionPort):
    @tool(
        "execute_librarian_graph",
        description="Use this tool to execute the Librarian Agent State Graph for handling document retrieval, insertion and updation related queries."
    )
    def execute_librarian_graph()->bool:
        """
        Tool function to execute the Librarian Agent State Graph
        Args:
            state (LibrarianState): Current state of the Librarian Agent
        Returns:
            bool: True if execution is successful, False otherwise
        """
        return executor.execute_librarian_agent_graph()
    return execute_librarian_graph