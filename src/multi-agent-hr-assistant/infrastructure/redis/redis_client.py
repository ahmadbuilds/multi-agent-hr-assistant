from infrastructure.redis.redis_config import get_redis_client
from domain.entities import AgentState
import json
redis=get_redis_client()

#function to save agent state to Redis
def save_agent_state_for_final_response(agent_state:AgentState):
    try:
        redis.set(
            f"user_id:{agent_state.user_id}:conversation_id:{agent_state.key}:state:agent:{agent_state.agent_name}",
            json.dumps(agent_state.state),
            ex=600
        )
    except Exception as e:
        print("Error saving agent state to Redis:", str(e))

#function to retrieve agent state from Redis
def get_agent_state_for_final_response(user_id:str, key:str, agent_name:str) -> dict:
    try:
        state_json = redis.get(f"user_id:{user_id}:conversation_id:{key}:state:agent:{agent_name}")
        if state_json:
            return json.loads(state_json)
        return {}
    except Exception as e:
        print("Error retrieving agent state from Redis:", str(e))
        return {}

#function to save the state of the agent for HITL intervention to Redis
def save_agent_state_for_hitl_intervention(agent_state:AgentState):
    try:
        redis.set(
            f"user_id:{agent_state.user_id}:conversation_id:{agent_state.key}:hitl_state",
            json.dumps(agent_state.state),
            ex=600
        )
    except Exception as e:
        print("Error saving HITL agent state to Redis:", str(e))

#function to retrieve the state of the agent for HITL intervention from Redis
def get_agent_state_for_hitl_intervention(user_id:str, key:str) -> dict:
    try:
        state_json = redis.get(f"user_id:{user_id}:conversation_id:{key}:hitl_state")
        if state_json:
            return json.loads(state_json)
        return {}
    except Exception as e:
        print("Error retrieving HITL agent state from Redis:", str(e))
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


#function to store the document hash in Redis
def save_document_version(updated_name:str)->bool:
    try:
        redis.set(f"document_version_name",updated_name)
        return True
    except Exception as e:
        print("Error saving document version name to Redis:", str(e))
        return False
    
#function to retrieve the document hash from Redis
def get_document_version()->str:
    try:
        version_name = redis.get(f"document_version_name")
        if version_name:
            return version_name
        return ""
    except Exception as e:
        print("Error retrieving document version name from Redis:", str(e))
        return ""
    
#function to save the document hash in Redis
def save_document_hash_to_redis(document_id:str, document_hash:str)->bool:
    try:
        #here document id is document version name
        redis.set(f"document_hash:{document_id}", document_hash)
        return True
    except Exception as e:
        print("Error saving document hash to Redis:", str(e))
        return False

#function to retrieve the document hash from Redis
def get_document_hash_to_redis(document_id:str)->str:
    try:
        document_hash = redis.get(f"document_hash:{document_id}")
        if document_hash:
            return document_hash
        return ""
    except Exception as e:
        print("Error retrieving document hash from Redis:", str(e))
        return ""

#function to delete the document hash from Redis
def delete_document_hash_to_redis(document_id:str)->bool:
    try:
        redis.delete(f"document_hash:{document_id}")
        return True
    except Exception as e:
        print("Error deleting document hash from Redis:", str(e))
        return False