# from infrastructure.llm_providers.ollama_provider import create_model_instance

# model=create_model_instance()

# print(model.invoke("Hello").content)

# from infrastructure.vector_store.chroma_client import create_chroma_instance
# from langchain_text_splitters import RecursiveCharacterTextSplitter


# vector_store=create_chroma_instance()
# print(vector_store)

from application.agents.clerk import ClerkAgent
from infrastructure.llm_providers.ollama_provider import create_model_instance
from infrastructure.adapters.clerk_leave_balance_adapter import ClerkLeaveBalanceAdapter
from infrastructure.adapters.clerk_ticket_creation_adapter import ClerkTicketCreationAdapter
#Creating LLM Model Instance
llm_model=create_model_instance()
#Creating Leave Balance Port Instance
leave_balance_port=ClerkLeaveBalanceAdapter()
#Creating Ticket Creation Port Instance
ticket_creation_port=ClerkTicketCreationAdapter()
#Creating Clerk Agent Instance
clerk_agent_instance=ClerkAgent(llm_model,leave_balance_port,ticket_creation_port)
#Creating Clerk Agent Graph
clerk_agent_graph=clerk_agent_instance.create_clerk_agent_graph()
#Displaying the Clerk Agent Graph
clerk_agent_instance.display_clerk_agent_graph(clerk_agent_graph)