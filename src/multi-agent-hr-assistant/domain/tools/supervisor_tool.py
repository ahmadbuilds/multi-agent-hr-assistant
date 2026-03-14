from domain.ports import ClerkGraphExecutionPort, LibrarianGraphExecutionPort
from langchain.tools import tool

def make_supervisor_execute_clerk_graph_tool(executor: ClerkGraphExecutionPort):
    @tool(
        "execute_clerk_graph",
        description="Use this tool to execute the Clerk Agent State Graph for handling HR related queries."
    )
    async def execute_clerk_graph() -> bool:
        return await executor.execute_clerk_agent_graph()
    return execute_clerk_graph

def make_supervisor_execute_librarian_graph_tool(executor: LibrarianGraphExecutionPort):
    @tool(
        "execute_librarian_graph",
        description="Use this tool to execute the Librarian Agent State Graph for handling document retrieval, insertion and updation related queries."
    )
    async def execute_librarian_graph() -> bool:
        return await executor.execute_librarian_agent_graph()
    return execute_librarian_graph