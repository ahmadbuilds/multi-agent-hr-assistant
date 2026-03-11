# from infrastructure.llm_providers.ollama_provider import create_model_instance

# model=create_model_instance()

# print(model.invoke("Hello").content)

# from infrastructure.vector_store.chroma_client import create_chroma_instance
# from langchain_text_splitters import RecursiveCharacterTextSplitter


# vector_store=create_chroma_instance()
# print(vector_store)

# from application.agents.clerk import ClerkAgent
from infrastructure.llm_providers.ollama_provider import create_model_instance
# from infrastructure.adapters.clerk_leave_balance_adapter import ClerkLeaveBalanceAdapter
# from infrastructure.adapters.clerk_ticket_creation_adapter import ClerkTicketCreationAdapter
# #Creating LLM Model Instance
# llm_model=create_model_instance()
# #Creating Leave Balance Port Instance
# leave_balance_port=ClerkLeaveBalanceAdapter()
# #Creating Ticket Creation Port Instance
# ticket_creation_port=ClerkTicketCreationAdapter()
# #Creating Clerk Agent Instance
# clerk_agent_instance=ClerkAgent(llm_model,leave_balance_port,ticket_creation_port)
# #Creating Clerk Agent Graph
# clerk_agent_graph=clerk_agent_instance.create_clerk_agent_graph()
# #Displaying the Clerk Agent Graph
# clerk_agent_instance.display_clerk_agent_graph(clerk_agent_graph)

# from application.agents.supervisor import SupervisorAgent
# from infrastructure.adapters.supervisor_clerk_graph_executor import SupervisorClerkGraphExecutor
# from application.states import SupervisorState
# llm_model=create_model_instance()
# SupervisorClerkGraphExecutorPort=SupervisorClerkGraphExecutor(SupervisorState)
# supervisor_agent_instance=SupervisorAgent(llm_model,SupervisorClerkGraphExecutorPort)
# supervisor_agent_graph=supervisor_agent_instance.create_supervisor_agent_graph()
# supervisor_agent_instance.build_supervisor_agent_graph_image(supervisor_agent_graph)

from application.agents.librarian import LibrarianAgent
from infrastructure.adapters.librarian_retrieval_adapter import LibrarianRetrievalAdapter
from infrastructure.adapters.librarian_insertion_adapter import LibrarianInsertionAdapter
from infrastructure.adapters.librarian_updation_adapter import LibrarianUpdateAdapter
from infrastructure.llm_providers.ollama_provider import create_model_instance
from infrastructure.adapters.chroma_store import ChromaVectorStore
from infrastructure.adapters.redis_store import RedisDocumentStore
from application.services.ingestion import IngestionService
#Creating LLM Model Instance
llm_model=create_model_instance()

#Creating Redis Document Store Port Instance
redis_store=RedisDocumentStore()
#Creating Chroma Vector Store Port Instance
vector_store=ChromaVectorStore()
#Creating Ingestion Service Instance
ingestion_service=IngestionService(redis_store,vector_store)

#Creating Librarian Agent Adapters
librarian_retrieval_adapter=LibrarianRetrievalAdapter()
librarian_insertion_adapter=LibrarianInsertionAdapter(ingestion_service)
librarian_update_adapter=LibrarianUpdateAdapter(ingestion_service)

#Creating Librarian Agent Instance
librarian_agent_instance=LibrarianAgent(llm_model,librarian_retrieval_adapter,librarian_insertion_adapter,librarian_update_adapter)
#Creating Librarian Agent Graph
librarian_agent_graph=librarian_agent_instance.create_librarian_agent_graph()
#Displaying the Librarian Agent Graph
librarian_agent_instance.display_librarian_agent_graph(librarian_agent_graph)