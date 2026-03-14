import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from fastapi import FastAPI, Header, HTTPException, status
from starlette.middleware.cors import CORSMiddleware
from domain.entities import UserQuery, TicketCreation
from infrastructure.supabase.supabase_client import (
    get_user_from_token,
    fetch_user_leave_balance,
    create_ticket_in_db,
    get_chat_history,
    save_message_to_db,
    is_chat_owned_by_user,
)
from infrastructure.redis.redis_client import publish_event
import asyncio
import socketio as sio_module
from infrastructure.socket.socket_manager import socket_manager
from infrastructure.socket.redis_to_socket_bridge import start_redis_to_socket_bridge as redis_to_socket_bridge
import json
from application.states import SupervisorState
from application.workflow import SupervisorWorkflow
from langchain_core.messages import HumanMessage, AIMessage

app = FastAPI()

combined_app = sio_module.ASGIApp(socket_manager, app)
combined_app = CORSMiddleware(
    combined_app,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    asyncio.create_task(redis_to_socket_bridge())

@app.post("/process_query")
async def process_query(user_query: UserQuery) -> dict:
    user = get_user_from_token(user_query.auth_token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid auth token")

    user_query.user_id = user.id

    if not is_chat_owned_by_user(user_query.conversation_id, user.id):
        raise HTTPException(status_code=403, detail="You do not have access to this chat")

    saved = save_message_to_db({
        "chat_id": user_query.conversation_id,
        "content": user_query.query,
        "type": "user",
        "attachment_url": user_query.attachment_url,
        "attachment_name": user_query.attachment_name,
    })
    if not saved:
        raise HTTPException(status_code=500, detail="Failed to save user message")

    # Fetch previous chat history and convert to LangChain message format
    chat_history = get_chat_history(user_query.conversation_id)
    chat_messages = [
        HumanMessage(content=msg["content"]) if msg["type"] == "user"
        else AIMessage(content=msg["content"])
        for msg in chat_history
    ]

    # Initialise and run the Supervisor workflow
    supervisor_state = SupervisorState(user_query=user_query, messages=chat_messages)
    workflow = SupervisorWorkflow(supervisor_state)
    final_response = await workflow.process_user_query(user_query)

    save_message_to_db({
        "chat_id": user_query.conversation_id,
        "content": final_response,
        "type": "ai",
    })

    return {"final_response": final_response}


@app.get("/leave_balance")
async def get_leave_balance_endpoint(authorization: str = Header(None)) -> dict:
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing")

    token = authorization.replace("Bearer ", "")
    user = get_user_from_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid auth token")

    balance = await fetch_user_leave_balance(user.id)
    return {"leave_balance": balance}


@app.post("/ticket_creation")
async def create_ticket_endpoint(
    ticket_data: TicketCreation,
    authorization: str = Header(None),
) -> dict:
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing")

    token = authorization.replace("Bearer ", "")
    user = get_user_from_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid auth token")

    ticket = ticket_data.dict()
    ticket["user_id"] = user.id
    created_ticket = await create_ticket_in_db(ticket)
    return {"status": created_ticket}


@app.post("/hitl_response", status_code=status.HTTP_202_ACCEPTED)
async def hitl_response(
    response_data: dict,
    authorization: str = Header(None),
) -> dict:
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing")

    token = authorization.replace("Bearer ", "")
    conversation_id = response_data.get("conversation_id")
    agent_name = response_data.get("agent_name", "Clerk")

    if not conversation_id:
        raise HTTPException(status_code=400, detail="conversation_id is required in the response data")

    user = get_user_from_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid auth token")

    response_channel = f"HITL_Response_Channel:{user.id}:{conversation_id}:{agent_name}"
    publish_event(response_channel, response_data)
    return {"status": "HITL response event published successfully"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:combined_app", host="0.0.0.0", port=8000, reload=True)