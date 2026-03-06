from abc import ABC,abstractmethod
from domain.entities import TicketCreation
from application.states import ClerkState, LibrarianState
#Interface for the Clerk Agent 
class LeaveBalancePort(ABC):

    #abstract method to get leave balance
    @abstractmethod
    def get_leave_balance(self, token:str)->int:
        """
        Method to get leave balance for the current logged in user
        Args:
            token (str): Authentication token of the user for whom to fetch the leave balance
        Returns:
            int: leave balance in days
        """
        pass
class TicketCreationPort(ABC):
    #abstract method to create a ticket
    @abstractmethod
    def create_ticket(self,ticket_data:TicketCreation,token:str)->bool:
        """
        Method to create a ticket based on the provided ticket data
        Args:
            ticket_data (TicketCreation): data required to create a ticket
            token (str): Authentication token of the user for whom to create the ticket
        Returns:
            bool: True if ticket creation is successful, False otherwise
        """
        pass

class ClerkGraphExecutionPort(ABC):
    @abstractmethod
    def execute_clerk_agent_graph(self,state:ClerkState)->bool:
        """
        Method to execute the Clerk Agent State Graph
        Args:
            state (ClerkState): Current state of the Clerk Agent
        Returns:
            bool: True if execution is successful, False otherwise
        """
        pass

class LibrarianGraphExecutionPort(ABC):
    @abstractmethod
    def execute_librarian_agent_graph(self,state:LibrarianState)->bool:
        """
        Method to execute the Librarian Agent State Graph
        Args:
            state (LibrarianState): Current state of the Librarian Agent
        Returns:
            bool: True if execution is successful, False otherwise
        """
        pass

class DocumentStorePort(ABC):
    @abstractmethod
    def get_document_hash(self,document_id:str)->str:
        """
        Method to get the hash of a document based on its ID
        Args:
            document_id (str): Unique identifier of the document
        Returns:
            str: Hash of the document
        """
        pass

    @abstractmethod
    def save_document_hash(self,document_id:str,document_hash:str)->bool:
        """
        Method to save the hash of a document with its ID
        Args:
            document_id (str): Unique identifier of the document
            document_hash (str): Hash of the document to be saved
        Returns:
            bool: True if saving is successful, False otherwise
        """
        pass

    @abstractmethod
    def delete_document_hash(self,document_id:str)->bool:
        """
        Method to delete the hash of a document based on its ID
        Args:
            document_id (str): Unique identifier of the document
        Returns:
            bool: True if deletion is successful, False otherwise
        """
        pass

class VectorStorePort(ABC):
    @abstractmethod
    def upsert_embeddings(self,chunks:list,metadata:list,ids:list)->bool:
        """
        Method to upsert document chunks and their metadata into the vector store
        Args:
            chunks (list): List of document chunks to be upserted
            metadata (list): List of metadata corresponding to each document chunk
            ids (list): List of IDs for each document chunk
        Returns:
            bool: True if upsert is successful, False otherwise
        """
        pass

    @abstractmethod
    def get_existing_chunk_hashes(self,document_hash:str)->list:
        """
        Method to get the existing chunk hashes from the vector store
        Args:
            document_hash (str): Hash of the document for which to fetch the chunk hashes
        Returns:
            list: List of existing chunk hashes in the vector store for the given document hash
        """
        pass

    @abstractmethod
    def delete_chunks_by_document_hash(self,document_hash:str)->bool:
        """
        Method to delete chunks from the vector store based on the document hash
        Args:
            document_hash (str): Hash of the document for which to delete the chunks
        Returns:
            bool: True if deletion is successful, False otherwise
        """
        pass