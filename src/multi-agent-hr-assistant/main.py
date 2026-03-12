import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from fastapi import FastAPI,Header,HTTPException,status
from starlette.middleware.cors import CORSMiddleware
from domain.entities import UserQuery, TicketCreation
from infrastructure.supabase.supabase_client import get_user_from_token,fetch_user_leave_balance,create_ticket_in_db
from infrastructure.redis.redis_client import publish_event
import asyncio
import socketio as sio_module
from infrastructure.socket.socket_manager import socket_manager, broadcast_hitl_event
from infrastructure.redis.redis_config import get_async_redis_client
import json
from application.states import SupervisorState
from application.workflow import SupervisorWorkflow
from infrastructure.supabase.supabase_client import get_chat_history,save_message_to_db
from langchain_core.messages import HumanMessage, AIMessage
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

combined_app = sio_module.ASGIApp(socket_manager, app)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(redis_listener())

async def redis_listener():
    redis = get_async_redis_client()
    pubsub = redis.pubsub()
    
    await pubsub.psubscribe("HITL_Intervention_Channel:*:*:*")
    
    print("Started Redis listener for HITL events...")
    
    async for message in pubsub.listen():
        if message["type"] == "pmessage":
            try:
                channel = message["channel"]
                data = json.loads(message["data"])
                
                # Extract user_id, conversation_id and agent_name from channel
                # Format: HITL_Intervention_Channel:{user_id}:{conversation_id}:{agent_name}
                parts = channel.split(":")
                if len(parts) >= 4:
                    user_id = parts[1]
                    conversation_id = parts[2]
                    agent_name = parts[3]
                    
                    # Broadcast via Socket.IO
                    await broadcast_hitl_event(user_id, conversation_id, agent_name, data)
            except Exception as e:
                print(f"Error processing Redis message: {e}")

@app.post("/process_query")
async def process_query(user_query:UserQuery)->dict:
    user=get_user_from_token(user_query.auth_token)
    if not user:
        return {"error":"Invalid auth token"}
    
    user_query.user_id=user.id

    #fetch the previous chat history using user_id and conversation_id
    chat_history=get_chat_history(user_query.conversation_id)
    #converting the chat history to the format required by the workflow
    chat_messages = [HumanMessage(content=msg["content"]) if msg["type"] == "user" else AIMessage(content=msg["content"]) for msg in chat_history]

    #initialize the Supervisor State
    supervisor_state=SupervisorState(user_query=user_query,messages=chat_messages)   

    #process the user query through the Supervisor Workflow
    workflow=SupervisorWorkflow(supervisor_state)

    final_response=workflow.process_user_query(user_query)

    #save the user query and final response to the database
    save_message_to_db({
        "chat_id": user_query.conversation_id,
        "content": final_response,
        "type": "ai"
    })

    return {"final_response": final_response}

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
    agent_name=response_data.get("agent_name", "Clerk")
    
    if not conversation_id:
        raise HTTPException(status_code=400, detail="conversation_id is required in the response data")
    
    #fetch the user details using the token
    user=get_user_from_token(token)
    
    #if user is not found, return an error
    if not user:
        raise HTTPException(status_code=401, detail="Invalid auth token")
    
    #if the user is found, store the HITL response in Redis for further processing
    response_channel=f"HITL_Response_Channel:{user.id}:{conversation_id}:{agent_name}"
    publish_event(response_channel,response_data)
    return {"status":"HITL response event published successfully"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:combined_app", host="0.0.0.0", port=8000, reload=True)
