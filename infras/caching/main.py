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