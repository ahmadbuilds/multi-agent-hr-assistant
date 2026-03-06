from domain.ports import LibrarianUpdatePort
from application.services.ingestion import IngestionService

class LibrarianUpdateAdapter(LibrarianUpdatePort):
    def __init__(self,ingestion_service:IngestionService):
        self.ingestion_service = ingestion_service
    
    def update_document(self, document_content:str)->bool:
        """
        Method to update an existing document based on the provided content
        Args:
            document_content (str): Content of the document to be updated
        Returns:
            bool: True if document update is successful, False otherwise
        """
        return self.ingestion_service.handle_policy_update(document_content)