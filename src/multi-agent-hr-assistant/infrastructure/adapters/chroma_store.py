from domain.ports import VectorStorePort
from infrastructure.vector_store.chroma_client import create_chroma_instance

class ChromaVectorStore(VectorStorePort):
    def __init__(self):
        self.vector_store=create_chroma_instance()

    def upsert_embeddings(self, chunks: list, metadata: list, ids: list) -> bool:
        """
        Method to upsert document chunks and their metadata into the vector store
        Args:
            chunks (list): List of document chunks to be upserted
            metadata (list): List of metadata corresponding to each document chunk
            ids (list): List of IDs for each document chunk
        Returns:
            bool: True if upserting is successful, False otherwise
        """
        try:
            self.vector_store.add_texts(texts=chunks, metadatas=metadata, ids=ids)
            return True
        except Exception as e:
            print(f"Error upserting embeddings: {e}")
            return False
        
    def get_existing_chunk_hashes(self, document_hash: str) -> list:
        """
        Method to get the existing chunk hashes from the vector store
        Args:
            document_hash (str): Hash of the document for which to fetch the chunk hashes
        Returns:
            list: List of existing chunk hashes for the given document hash
        """
        try:
            result = self.vector_store.get(where={"document_hash":document_hash},include=["metadatas","documents"])
            if result and "metadatas" in result and result["metadatas"]:
                chunk_hashes = [metadata.get("chunk_hash") for metadata in result["metadatas"] if "chunk_hash" in metadata]
                return chunk_hashes
            return []
        except Exception as e:
            print(f"Error fetching existing chunk hashes: {e}")
            return []
        
    def delete_chunks_by_chunk_hash(self, chunk_hash: str) -> bool:
        """
        Method to delete chunks from the vector store based on the chunk hash
        Args:
            chunk_hash (str): Hash of the chunk for which to delete the corresponding chunks from the vector store
        Returns:
            bool: True if deletion is successful, False otherwise
        """
        try:
            result = self.vector_store.get(where={"chunk_hash": chunk_hash},include=["metadatas","documents"])
            if result and "ids" in result and result["ids"]:
                ids_to_delete = result["ids"]
                self.vector_store.delete(ids=ids_to_delete)
            return True
        except Exception as e:
            print(f"Error deleting chunks by chunk hash: {e}")
            return False