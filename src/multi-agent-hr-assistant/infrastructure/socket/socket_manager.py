import socketio

socket_manager = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins='*')

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

async def broadcast_hitl_event(user_id: str, conversation_id: str, event_data: dict):
    """
    Broadcasts a HITL event to a specific channel/room.
    The channel name format matches the frontend expectation:
    HITL_Intervention_Channel:{user_id}:{conversation_id}:Clerk
    """
    channel = f"HITL_Intervention_Channel:{user_id}:{conversation_id}:Clerk"
    print(f"Broadcasting HITL event to {channel}: {event_data}")
    #emit the event with the name of the channel so the frontend can listen specifically to it
    await socket_manager.emit(channel, {"event_data": event_data})
    
    # emit a generic 'message' event for fallback listeners
    await socket_manager.emit('message', {"channel": channel, "event_data": event_data})
