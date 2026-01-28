from abc import ABC,abstractmethod
from domain.entities import TicketCreation
#Interface for the Clerk Agent 
class LeaveBalancePort(ABC):

    #abstract method to get leave balance
    @abstractmethod
    def get_leave_balance(self)->int:
        """
        Method to get leave balance for the current logged in user
        Returns:
            int: leave balance in days
        """
        pass
class TicketCreationPort(ABC):
    #abstract method to create a ticket
    @abstractmethod
    def create_ticket(self,ticket_data:TicketCreation)->bool:
        """
        Method to create a ticket based on the provided ticket data
        Args:
            ticket_data (TicketCreation): data required to create a ticket
        Returns:
            bool: True if ticket creation is successful, False otherwise
        """
        pass