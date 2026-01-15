from abc import ABC,abstractmethod


#Interface for the Document Ingestion
class IDocumentIngestor(ABC):
    """
    Abstract base class for ChromaDB vector store database operations.
    """

    @abstractmethod
    def add_documents(self, documents: list):
        """
        Add documents to the vector store.
        :param documents: List of documents to be added.
        """
        pass

    @abstractmethod
    def delete_documents(self):
        """
        Delete Documents from the vector store
        """
        pass

    @abstractmethod
    def update_documents(self):
        """ 
        Update Documents from the vector store
        """
        pass
    
    @abstractmethod
    def delete_all_documents():
        """
        Delete all the documents from the vector store
        """
        pass