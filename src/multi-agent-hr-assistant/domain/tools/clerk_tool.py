from langchain.tools import tool 
from domain.ports import LeaveBalancePort

#wrapper function to get leave balance using the LeaveBalancePort
def make_get_leave_balance_tool(leave_balance_port:LeaveBalancePort):
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
        return leave_balance_port.get_leave_balance()
    
    return get_leave_balance