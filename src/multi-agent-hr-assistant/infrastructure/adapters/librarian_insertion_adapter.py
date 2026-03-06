from domain.ports import LibrarianInsertionPort
from application.services.ingestion import IngestionService

class LibrarianInsertionAdapter(LibrarianInsertionPort):
    def __init__(self,ingestion_service:IngestionService):
        self.ingestion_service = ingestion_service
    
    def insert_document(self, document_content:str)->bool:
        """
        Method to insert a new document based on the provided content
        Args:
            document_content (str): Content of the document to be inserted
        Returns:
            bool: True if document insertion is successful, False otherwise
        """
        return self.ingestion_service.handle_new_policy_upload(document_content)