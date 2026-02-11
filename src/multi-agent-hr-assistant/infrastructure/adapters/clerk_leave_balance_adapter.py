from domain.ports import LeaveBalancePort
import requests
from config import CLERK_API_KEY
#Adapter class to interact with Clerk Leave Balance API
class ClerkLeaveBalanceAdapter(LeaveBalancePort):
    def __init__(self):
        self.api_key = CLERK_API_KEY
    def get_leave_balance(self, token:str) -> int:
        """
        Method to get leave balance for the current logged in user
        Args:
            token (str): Authentication token of the user for whom to fetch the leave balance
        Returns:
            int: leave balance in days
        """
        try:
            response = requests.get(f"{self.api_key}/leave_balance", headers={"Authorization": f"Bearer {token}"})
            response.raise_for_status()
            data = response.json()
            return data.get("leave_balance", 0)
        except requests.RequestException:
            print("Error fetching leave balance from Clerk API")
            return 0