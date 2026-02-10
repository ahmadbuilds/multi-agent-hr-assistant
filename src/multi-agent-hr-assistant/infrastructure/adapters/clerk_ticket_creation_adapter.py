from domain.ports import TicketCreationPort
from domain.entities import TicketCreation
from config import CLERK_API_KEY
import requests

#Adapter class to interact with Clerk Ticket Creation API
class ClerkTicketCreationAdapter(TicketCreationPort):
    def __init__(self):
        self.clerk_api_key=CLERK_API_KEY

    def create_ticket(self,ticket_data:TicketCreation,user_id:str) -> bool:
        """
        Method to create a ticket based on the provided ticket data
        Args:
            ticket_data (TicketCreation): data required to create a ticket
        Returns:
            bool: True if ticket creation is successful, False otherwise
        """
        try:
            ticket_data_dict=ticket_data.model_dump()
            ticket_data_dict["user_id"]=user_id
            response=requests.post(f"{self.clerk_api_key}/ticket_creation",json=ticket_data_dict)
            response.raise_for_status()
            data=response.json()
            return data.get("status",False)
        except Exception as e:
            print(f"Error creating ticket: {e}")
            return False