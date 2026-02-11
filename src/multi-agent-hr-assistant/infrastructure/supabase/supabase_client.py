from supabase import create_client,Client
from config import key,url

supabase:Client=create_client(url,key)

#function to get user details from supabase using auth token
def get_user_from_token(token:str):
    try:
        response=supabase.auth.get_user(token)
        return response.user
    except Exception as e:
        print("Error retrieving user from token:", str(e))
        return None
    
#function to get the previous chat history using user_id and conversation_id
def get_chat_history(conversation_id:str)->list:
    try:
        response=supabase.table("messages").select("*").eq("conversation_id", conversation_id).order("created_at", desc=False).execute()
        return response.data
    except Exception as e:
        print("Error retrieving chat history:", str(e))
        return []
    
#function to get the leave balance for a user using user_id
def fetch_user_leave_balance(user_id:str)->int:
    try:
        response=supabase.table("leave_balances").select("balance").eq("user_id", user_id).single().execute()
        if response.data:
            return response.data.get("balance", 0)
        return 0
    except Exception as e:
        print("Error retrieving leave balance:", str(e))
        return 0
    
#function to create a ticket in the database
def create_ticket_in_db(ticket_data:dict)->bool:
    try:
        response=supabase.table("tickets").insert(ticket_data).execute()
        return len(response.data)>0
    except Exception as e:
        print("Error creating ticket in database:", str(e))
        return False