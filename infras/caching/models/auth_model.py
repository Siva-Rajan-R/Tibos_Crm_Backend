from ..main import redis_client,set_redis,get_redis,unlink_redis
import os,json
from icecream import ic

# When the user role,pass,name are change this cache will trigger
async def set_auth_revoke(user_id:str):
    KEY=f"AUTH-REVOKE-{user_id}"
    await set_redis(key=KEY,value=user_id,expire=60*60*30)
    return KEY

async def get_auth_revoke(user_id:str):
    KEY=f"AUTH-REVOKE-{user_id}"
    return await get_redis(key=KEY)

async def unlink_auth_revoke(user_id:str):
    KEY=f"AUTH-REVOKE-{user_id}"
    return await unlink_redis(keys=[KEY])

# When the forgot pass was requested this cache will be triggered
async def set_auth_forgot(ip:str,data:dict):
    KEY=f"AUTH-FORGOT-{ip}"
    await set_redis(key=KEY,value=data,expire=1500)
    return KEY

async def get_auth_forgot(ip:str):
    KEY=f"AUTH-FORGOT-{ip}"
    return await get_redis(key=KEY)

async def unlink_auth_forgot(ip:str):
    KEY=f"AUTH-FORGOT-{ip}"
    return await unlink_redis(keys=[KEY])
