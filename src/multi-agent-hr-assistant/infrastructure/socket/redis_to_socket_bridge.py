import asyncio
import json
from infrastructure.redis.redis_config import get_async_redis_client
from infrastructure.socket.socket_manager import broadcast_hitl_event


async def start_redis_to_socket_bridge():
    """
    Runs forever as a background asyncio task.
    Pattern-subscribes to HITL_Intervention_Channel:* on Redis and
    forwards every message to the Socket.IO layer.
    """
    #print("[BRIDGE] Redis→Socket.IO bridge starting...")

    while True: 
        redis = None
        pubsub = None
        try:
            redis = get_async_redis_client()
            pubsub = redis.pubsub()

            await pubsub.psubscribe("HITL_Intervention_Channel:*")
            # print("[BRIDGE] Subscribed to pattern 'HITL_Intervention_Channel:*'")

            async for message in pubsub.listen():
                msg_type = message.get("type")

                if msg_type in ("psubscribe", "punsubscribe"):
                    continue

                if msg_type == "pmessage":
                    channel: str = message.get("channel", "")
                    raw_data = message.get("data", "{}")

                    # print(f"[BRIDGE] Received message on channel '{channel}'")

                    try:
                        event_data: dict = json.loads(raw_data)
                    except (json.JSONDecodeError, TypeError) as parse_err:
                        print(f"[BRIDGE] Failed to parse message data: {parse_err}  raw={raw_data!r}")
                        continue

                    # Channel format: HITL_Intervention_Channel:{user_id}:{conversation_id}:{agent_name}
                    parts = channel.split(":")
                    if len(parts) != 4:
                        print(f"[BRIDGE] Unexpected channel format — skipping: '{channel}'")
                        continue

                    _, user_id, conversation_id, agent_name = parts

                    try:
                        await broadcast_hitl_event(
                            user_id=user_id,
                            conversation_id=conversation_id,
                            agent_name=agent_name,
                            event_data=event_data,
                        )
                        # print(f"[BRIDGE] Forwarded HITL event: user={user_id} conv={conversation_id} agent={agent_name}")
                    except Exception as emit_err:
                        print(f"[BRIDGE] Socket.IO emit failed: {emit_err}")

        except asyncio.CancelledError:
            print("[BRIDGE] Bridge task cancelled — shutting down cleanly")
            break

        except Exception as err:
            print(f"[BRIDGE] Unexpected error: {err} — reconnecting in 3 s")
            await asyncio.sleep(3)

        finally:
            try:
                if pubsub:
                    await pubsub.punsubscribe("HITL_Intervention_Channel:*")
                if redis:
                    await redis.aclose()
            except Exception:
                pass