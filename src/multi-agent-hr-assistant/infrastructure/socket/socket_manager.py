import socketio

socket_manager = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins=[])

socket_app = socketio.ASGIApp(socket_manager)

@socket_manager.event
async def connect(sid, environ):
    print(f"Client connected: {sid}")

@socket_manager.event
async def disconnect(sid):
    print(f"Client disconnected: {sid}")

@socket_manager.event
async def join_room(sid, room):
    await socket_manager.enter_room(sid, room)
    print(f"Client {sid} joined room: {room}")

async def broadcast_hitl_event(user_id: str, conversation_id: str, agent_name: str, event_data: dict):
    """
    Broadcasts a HITL event directly to connected Socket.IO clients.
    """
    channel = f"HITL_Intervention_Channel:{user_id}:{conversation_id}:{agent_name}"
    print(f"[SOCKET] Broadcasting HITL event to channel '{channel}'")
    print(f"[SOCKET] Payload being emitted: {event_data}")


    await socket_manager.emit(channel, event_data)

    await socket_manager.emit('message', {"channel": channel, "event_data": event_data})

    print(f"[SOCKET] Emit complete for channel '{channel}'")