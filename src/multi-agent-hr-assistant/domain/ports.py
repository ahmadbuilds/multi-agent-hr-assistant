from abc import ABC,abstractmethod
from domain.entities import TicketCreation
from application.states import ClerkState, LibrarianState
#Interface for the Clerk Agent 
class LeaveBalancePort(ABC):

    #abstract method to get leave balance
    @abstractmethod
    def get_leave_balance(self, user_id: str)->int:
        """
        Method to get leave balance for the current logged in user
        Args:
            user_id (str): ID of the user for whom to fetch the leave balance
        Returns:
            int: leave balance in days
        """
        pass
class TicketCreationPort(ABC):
    #abstract method to create a ticket
    @abstractmethod
    def create_ticket(self,ticket_data:TicketCreation,user_id:str)->bool:
        """
        Method to create a ticket based on the provided ticket data
        Args:
            ticket_data (TicketCreation): data required to create a ticket
        Returns:
            bool: True if ticket creation is successful, False otherwise
        """
        pass

class ClerkGraphExecutionPort(ABC):
    @abstractmethod
    def execute_clerk_agent_graph(self,state:ClerkState)->None:
        """
        Method to execute the Clerk Agent State Graph
        Args:
            state (ClerkState): Current state of the Clerk Agent
        Returns:
            None
        """
        pass

class LibrarianGraphExecutionPort(ABC):
    @abstractmethod
    def execute_librarian_agent_graph(self,state:LibrarianState)->None:
        """
        Method to execute the Librarian Agent State Graph
        Args:
            state (LibrarianState): Current state of the Librarian Agent
        Returns:
            None
        """
        pass