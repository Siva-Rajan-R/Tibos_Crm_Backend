from ..main import redis_client
import os,json
from icecream import ic
    

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

async def unlink_redis(key:list):
    try:
        result = await redis_client.unlink(*key)
        ic(f"✅ Unlinked Redis keys: {key}. Result: {result}")
        return result
    except Exception as e:
        ic(f"❌ Failed to unlink Redis key: {key}. Error: {e}")
        return None