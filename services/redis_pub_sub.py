import json
import asyncio
from infras.caching.main import redis_client
from .sse import sse_manager
from icecream import ic

async def redis_listener():

    pubsub = redis_client.pubsub()
    await pubsub.subscribe("sse_channel")

    async for message in pubsub.listen():
        ic(message)
        if message["type"] != "message":
            continue

        payload = json.loads(message["data"])

        client_id = payload["client_id"]
        data = payload["data"]

        await sse_manager.send(client_id, data)


async def notify(client_id, data):
    payload = {
        "client_id": client_id,
        "data": data
    }

    await redis_client.publish(
        "sse_channel",
        json.dumps(payload)
    )