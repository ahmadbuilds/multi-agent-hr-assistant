from supabase import create_client,Client
from config import key,url,service_key

supabase:Client=create_client(url,key)
_service_supabase:Client=create_client(url,service_key)

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
        response=supabase.table("messages").select("*").eq("chat_id", conversation_id).order("created_at", desc=False).execute()
        return response.data
    except Exception as e:
        print("Error retrieving chat history:", str(e))
        return []
    
#function to save messages to the database
def save_message_to_db(message_data:dict)->bool:
    try:
        response=_service_supabase.table("messages").insert(message_data).execute()
        return len(response.data)>0
    except Exception as e:
        print("Error saving message to database:", str(e))
        return False

def is_chat_owned_by_user(chat_id:str,user_id:str)->bool:
    try:
        response=_service_supabase.table("chats").select("chat_id").eq("chat_id", chat_id).eq("user_id", user_id).limit(1).execute()
        return len(response.data)>0
    except Exception as e:
        print("Error validating chat ownership:", str(e))
        return False

#function to get the leave balance for a user using user_id
async def fetch_user_leave_balance(user_id:str)->int:
    try:
        response=_service_supabase.table("leave_balance").select("balance").eq("user_id", user_id).maybe_single().execute()
        if response.data:
            return response.data.get("balance", 0)
        return 0
    except Exception as e:
        print("Error retrieving leave balance:", str(e))
        return 0
    
#function to create a ticket in the database
async def create_ticket_in_db(ticket_data:dict)->bool:
    try:
        db_payload = {
            k: v for k, v in ticket_data.items()
            if k not in {"accepted"} and v is not None
        }
        response=_service_supabase.table("tickets").insert(db_payload).execute()
        return len(response.data)>0
    except Exception as e:
        print("Error creating ticket in database:", str(e))
        return False