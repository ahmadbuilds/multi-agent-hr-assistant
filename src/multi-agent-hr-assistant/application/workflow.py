from application.agents.supervisor import SupervisorAgent
from infrastructure.adapters.supervisor_clerk_graph_executor import SupervisorClerkGraphExecutor
from infrastructure.adapters.Supervisor_librarian_graph_executor import SupervisorLibrarianGraphExecutor
from application.states import SupervisorState,ClerkState,LibrarianState
from infrastructure.llm_providers.groq_provider import create_model_instance
from domain.ports import ClerkGraphExecutionPort, LibrarianGraphExecutionPort
from domain.entities import UserQuery
class SupervisorWorkflow:
    def __init__(self,supervisor_state:SupervisorState):
        self.supervisor_state=supervisor_state
        self.llm_model=create_model_instance()
        self.SupervisorClerkGraphExecutorPort: ClerkGraphExecutionPort = SupervisorClerkGraphExecutor(ClerkState)
        self.SupervisorLibrarianGraphExecutorPort: LibrarianGraphExecutionPort = SupervisorLibrarianGraphExecutor(LibrarianState)
        self.supervisor_agent_instance=SupervisorAgent(self.llm_model,self.SupervisorClerkGraphExecutorPort,self.SupervisorLibrarianGraphExecutorPort)

        self.compiled_supervisor_graph=self.supervisor_agent_instance.create_supervisor_agent_graph()
    def process_user_query(self,user_query:UserQuery)->str:
        try:
            #Invoking the Supervisor Agent to process the user query and execute the respective agent graphs based on the identified intents in the user query
            result=self.compiled_supervisor_graph.invoke(self.supervisor_state)
            return result["final_response"]
        except Exception as e:
            raise RuntimeError(f"Failed to process user query in workflow: {str(e)}")