from domain.ports import LibrarianGraphExecutionPort
from application.states import LibrarianState
from infrastructure.llm_providers.ollama_provider import create_model_instance
from infrastructure.adapters.librarian_retrieval_adapter import LibrarianRetrievalAdapter
from infrastructure.adapters.librarian_insertion_adapter import LibrarianInsertionAdapter
from infrastructure.adapters.librarian_updation_adapter import LibrarianUpdateAdapter
from application.agents.librarian import LibrarianAgent
from infrastructure.redis.redis_client import save_agent_state_for_final_response
from domain.entities import AgentState
from application.services.ingestion import IngestionService
from infrastructure.adapters.chroma_store import ChromaVectorStore
from infrastructure.adapters.redis_store import RedisDocumentStore
class SupervisorLibrarianGraphExecutor(LibrarianGraphExecutionPort):
    def __init__(self,state:LibrarianState):
        self.librarian_state=state
        self.chroma_store=ChromaVectorStore()
        self.redis_store=RedisDocumentStore()
        self.ingestion_service=IngestionService(self.redis_store,self.chroma_store)

    #function to update the state of librarian
    def update_librarian_state(self,state:LibrarianState):
        self.librarian_state=state

    #Method to execute the Librarian Agent State Graph
    def execute_librarian_agent_graph(self)->bool:
        agent_state=None
        try:
            llm_model=create_model_instance("orca-mini:3b")
            retrieval_port=LibrarianRetrievalAdapter()
            insertion_port=LibrarianInsertionAdapter(self.ingestion_service)
            updation_port=LibrarianUpdateAdapter(self.ingestion_service)
            librarian_agent=LibrarianAgent(llm_model,retrieval_port,insertion_port,updation_port)

            #Creating the Librarian Agent Graph
            librarian_graph=librarian_agent.create_librarian_agent_graph()
            
            #Agent State to be saved in Redis before execution
            agent_state=AgentState(
                user_id=self.librarian_state.user_query.user_id,
                key=self.librarian_state.user_query.conversation_id,
                agent_name="Librarian",
                state={
                    "status":"initialized",
                    "final_response":"",
                    "error":None
                }
            )

            #calling the Redis function to save the initial state of the Librarian Agent before execution
            save_agent_state_for_final_response(agent_state)

            agent_state.state["status"]="running"
            save_agent_state_for_final_response(agent_state)

            #Executing the Librarian Agent Graph
            librarian_graph.invoke(self.librarian_state)

            agent_state.state["status"]="completed"
            save_agent_state_for_final_response(agent_state)

            return True
        except Exception as e:
            if agent_state:
                agent_state.state["status"]="error"
                agent_state.state["error"]=str(e)
                save_agent_state_for_final_response(agent_state)
            raise RuntimeError(f"Failed to execute Librarian Agent Graph: {str(e)}")