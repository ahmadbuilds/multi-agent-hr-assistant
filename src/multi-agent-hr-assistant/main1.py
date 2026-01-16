# from infrastructure.llm_providers.ollama_provider import create_model_instance

# model=create_model_instance()

# print(model.invoke("Hello").content)

from infrastructure.vector_store.chroma_client import create_chroma_instance
from langchain_text_splitters import RecursiveCharacterTextSplitter


vector_store=create_chroma_instance()
print(vector_store)