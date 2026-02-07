from infrastructure.redis.redis_config import get_redis_client
from domain.entities import AgentState
import json
redis=get_redis_client()

#function to save agent state to Redis
def save_agent_state(agent_state:AgentState):
    try:
        redis.set(
            agent_state.user_id,
            f"user_id:{agent_state.user_id}:conversation_id:{agent_state.key}:state",
            json.dumps(agent_state.state)
        )
    except Exception as e:
        print("Error saving agent state to Redis:", str(e))

#function to retrieve agent state from Redis
def get_agent_state(user_id:str, key:str) -> dict:
    try:
        state_json = redis.get(f"user_id:{user_id}:conversation_id:{key}:state")
        if state_json:
            return json.loads(state_json)
        return {}
    except Exception as e:
        print("Error retrieving agent state from Redis:", str(e))
        return {}

#function to delete agent state from redis based on user_id and key
def delete_agent_state(user_id:str, key:str):
    try:
        redis.delete(f"user_id:{user_id}:conversation_id:{key}:state")
    except Exception as e:
        print("Error deleting agent state from Redis:", str(e))

#function to publish and event to a Redis channel for inter-agent communication
def publish_event(channel:str, event_data:dict):
    try:
        redis.publish(channel, json.dumps(event_data))
    except Exception as e:
        print("Error publishing event to Redis channel:", str(e))