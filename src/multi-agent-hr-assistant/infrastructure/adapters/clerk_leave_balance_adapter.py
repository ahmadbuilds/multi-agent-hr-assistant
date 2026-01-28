from domain.ports import LeaveBalancePort
import requests
from config import CLERK_API_URL
#Adapter class to interact with Clerk Leave Balance API
class ClerkLeaveBalanceAdapter(LeaveBalancePort):
    def __init__(self):
        self.api_url = CLERK_API_URL
    def get_leave_balance(self) -> int:
        """
        Method to get leave balance for the current logged in user
        Returns:
            int: leave balance in days
        """
        try:
            response = requests.get(f"{self.api_url}/leave_balance")
            response.raise_for_status()
            data = response.json()
            return data.get("leave_balance", 0)
        except requests.RequestException:
            print("Error fetching leave balance from Clerk API")
            return 0