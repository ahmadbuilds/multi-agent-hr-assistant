from fastapi import FastAPI,Header,HTTPException,status
from fastapi.middleware.cors import CORSMiddleware
from domain.entities import UserQuery,TicketCreation
from infrastructure.supabase.supabase_client import get_user_from_token,fetch_user_leave_balance,create_ticket_in_db
from infrastructure.redis.redis_client import publish_event
import asyncio
from infrastructure.socket.socket_manager import socket_app, broadcast_hitl_event
from infrastructure.redis.redis_config import get_redis_client
import json

app = FastAPI()

# Mount Socket.IO app
app.mount("/socket.io", socket_app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(redis_listener())

async def redis_listener():
    redis = get_redis_client()
    pubsub = redis.pubsub()
    
    await pubsub.psubscribe("HITL_Intervention_Channel:*:*:Clerk")
    
    print("Started Redis listener for HITL events...")
    
    async for message in pubsub.listen():
        if message["type"] == "pmessage":
            try:
                channel = message["channel"]
                data = json.loads(message["data"])
                
                # Extract user_id and conversation_id from channel
                parts = channel.split(":")
                if len(parts) >= 4:
                    user_id = parts[1]
                    conversation_id = parts[2]
                    
                    # Broadcast via Socket.IO
                    await broadcast_hitl_event(user_id, conversation_id, data)
            except Exception as e:
                print(f"Error processing Redis message: {e}")

@app.post("/process_query")
async def process_query(user_query:UserQuery)->dict:
    user=get_user_from_token(user_query.auth_token)
    if not user:
        return {"error":"Invalid auth token"}
    
    user_query.user_id=user.id

@app.get("/leave_balance")
async def get_leave_balance_endpoint(authorization:str=Header(None))->dict:
    #check if the header contains the authorization token
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing")
    
    token=authorization.replace("Bearer ","")

    #fetch the user details using the token
    user=get_user_from_token(token)
    
    #if user is not found, return an error
    if not user:
        raise HTTPException(status_code=401, detail="Invalid auth token")
    
    #if the user is found, fetch the leave balance using the user_id and return it
    balance=await fetch_user_leave_balance(user.id)
    return {"leave_balance": balance}

@app.post("/ticket_creation")
async def create_ticket_endpoint(ticket_data:TicketCreation,authorization:str=Header(None))->dict:
    #check if the header contains the authorization token
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing")
    
    token=authorization.replace("Bearer ","")

    #fetch the user details using the token
    user=get_user_from_token(token)
    
    #if user is not found, return an error
    if not user:
        raise HTTPException(status_code=401, detail="Invalid auth token")
    
    #if the user is found, create the ticket using the user_id and return the ticket details
    ticket=ticket_data.dict()
    ticket["user_id"]=user.id
    created_ticket=await create_ticket_in_db(ticket)
    return {"status": created_ticket}

@app.post("/hitl_response",status_code=status.HTTP_202_ACCEPTED)
async def hitl_response(response_data:dict,authorization:str=Header(None))->dict:
    #check if the header contains the authorization token
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing")
    
    token=authorization.replace("Bearer ","")
    conversation_id=response_data.get("conversation_id")
    
    if not conversation_id:
        raise HTTPException(status_code=400, detail="conversation_id is required in the response data")
    
    #fetch the user details using the token
    user=get_user_from_token(token)
    
    #if user is not found, return an error
    if not user:
        raise HTTPException(status_code=401, detail="Invalid auth token")
    
    #if the user is found, store the HITL response in Redis for further processing
    response_channel=f"HITL_Response_Channel:{user.id}:{conversation_id}:Clerk"
    publish_event(response_channel,response_data)
    return {"status":"HITL response event published successfully"}
