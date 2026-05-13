import json
import asyncio
from infras.caching.main import redis_client
from .sse import sse_manager
from icecream import ic

async def redis_listener():
    ic("📡 Starting Redis Pub/Sub listener on 'sse_channel'...")
    while True:
        try:
            pubsub = redis_client.pubsub()
            await pubsub.subscribe("sse_channel")
            ic("✅ Subscribed to 'sse_channel'")

            async for message in pubsub.listen():
                if message["type"] != "message":
                    continue

                try:
                    payload = json.loads(message["data"])
                    client_id = payload.get("client_id")
                    data = payload.get("data")

                    if client_id and data:
                        ic(f"📩 Redis listener relaying message to {client_id}")
                        success = await sse_manager.send(client_id, data)
                        if not success:
                            ic(f"⚠️ SSE delivery failed for {client_id} (not connected?)")
                    else:
                        ic(f"⚠️ Invalid payload: {payload}")
                except Exception as e:
                    ic(f"❌ Error processing message: {e}")
                    
        except Exception as e:
            ic(f"❌ Redis listener connection error: {e}")
            await asyncio.sleep(5)  # Retry after 5 seconds


async def notify(client_id, data):
    payload = {
        "client_id": client_id,
        "data": data
    }

    await redis_client.publish(
        "sse_channel",
        json.dumps(payload)
    )