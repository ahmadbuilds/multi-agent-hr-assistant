from langchain.tools import tool 
from domain.ports import LeaveBalancePort, TicketCreationPort
from domain.entities import TicketCreation

#wrapper function to get leave balance using the LeaveBalancePort
def make_get_leave_balance_tool(leave_balance_port:LeaveBalancePort,token:str):
    @tool(
        name="get_balance",
        description="Use this tool to get the leave balance of the current logged in user. No input is required."
    )
    def get_leave_balance() -> int:
        """
        Tool function to get leave balance for the current logged in user
        Returns:
            int: leave balance in days
        """
        return leave_balance_port.get_leave_balance(token)
    
    return get_leave_balance

#wrapper function to create the Clerk Agent Get Balance Tool
def make_ticket_creation_tool(ticket_creation_port:TicketCreationPort,ticket_data:TicketCreation,token:str):
    @tool(
        name="clerk_create_ticket",
        description="Use this tool to create a ticket for the current logged in user. Input should include subject and description."
    )
    def create_ticket() -> bool:
        """
        Tool function to create a ticket for the current logged in user
        Returns:
            bool: True if ticket creation is successful, False otherwise
        """
        return ticket_creation_port.create_ticket(ticket_data,token)
    
    return create_ticket