from redis.asyncio import Redis
import os,json
from core.settings import SETTINGS
from icecream import ic

redis_client=Redis.from_url(SETTINGS.REDIS_URL,decode_responses=True)


async def check_redis_health():
    try:
        ic("🔃 Performing Redis health check...")
        pong = await redis_client.ping()
        ic(pong)
        if pong:
            ic("✅ Redis is connected and ready.")
            return True
        ic("❌ Redis health check failed: No pong response.")
        return False
    except Exception as e:
        ic(f"❌ Redis health check failed: {e}")
        return False
    

async def set_redis(key:str, value, expire:int=None):
    try:
        value=json.dumps(value)
        await redis_client.set(name=key, value=value, ex=expire)
        ic(f"✅ Set Redis key: {key} with value: {value} and expire: {expire}")
        return True
    except Exception as e:
        ic(f"❌ Failed to set Redis key: {key}. Error: {e}")
        return False

async def get_ttl_redis(key:str):
    try:
        ttl = await redis_client.ttl(name=key)
        ic(f"✅ TTL for Redis key: {key} is {ttl} seconds")
        return ttl
    except Exception as e:
        ic(f"❌ Failed to get TTL for Redis key: {key}. Error: {e}")
        return None

async def get_redis(key:str):
    try:
        value = await redis_client.get(name=key)
        value = json.loads(value) if value else None
        ic(f"✅ Retrieved Redis key: {key} with value: {value}")
        return value
    except Exception as e:
        ic(f"❌ Failed to get Redis key: {key}. Error: {e}")
        return None

async def unlink_redis(keys:list):
    try:
        result = await redis_client.unlink(*keys)
        ic(f"✅ Unlinked Redis keys: {keys}. Result: {result}")
        return result
    except Exception as e:
        ic(f"❌ Failed to unlink Redis key: {keys}. Error: {e}")
        return None