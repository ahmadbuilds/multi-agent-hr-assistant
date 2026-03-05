from domain.ports import VectorStorePort
from infrastructure.vector_store.chroma_client import create_chroma_instance

class ChromaVectorStore(VectorStorePort):
    def __init__(self):
        self.vector_store=create_chroma_instance()

    def upsert_embeddings(self, chunks: list, metadata: list) -> bool:
        """
        Method to upsert document chunks and their metadata into the vector store
        Args:
            chunks (list): List of document chunks to be upserted
            metadata (list): List of metadata corresponding to each document chunk
        Returns:
            bool: True if upserting is successful, False otherwise
        """
        try:
            self.vector_store.add_texts(documents=chunks, metadatas=metadata)
            return True
        except Exception as e:
            print(f"Error upserting embeddings: {e}")
            return False