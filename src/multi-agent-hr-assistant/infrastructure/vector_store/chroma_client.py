from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

#function to create the instance of the vector store
def create_chroma_instance(persist_dir:str='./data/policies')->Chroma:
    #creating Hugging Face Embedding model
    embedding_model=HuggingFaceEmbeddings(model="sentence-transformers/all-mpnet-base-v2")

    vector_store=Chroma(
        collection_name='policy_docs',
        embedding_function=embedding_model,
        persist_directory=persist_dir,
    )
    return vector_store