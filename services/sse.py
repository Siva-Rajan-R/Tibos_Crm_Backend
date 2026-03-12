import asyncio
from typing import Optional
from icecream import ic
import json
from infras.caching.main import set_redis,get_redis,unlink_redis

class SSEManager:

    def __init__(self):
        self.connections = {}

    async def create(self, client_id):

        if client_id in self.connections:
            return {
                "queue": self.connections[client_id],
                "send_greet": False
            }

        q = asyncio.Queue()
        self.connections[client_id] = q

        return {
            "queue": q,
            "send_greet": True
        }

    async def send(self, client_id, data):
        ic(self.connections)
        queue = self.connections.get(client_id)
        ic(queue)
        if queue:
            await queue.put(data)
            return True
        else:
            return False

    async def remove(self, client_id):
        self.connections.pop(client_id, None)


def sse_msg_builder(title:str,description:str,type:str,url:Optional[str]=None):
    return {
        'title':title,
        'description':description,
        'type':type,
        'url':url
    }

sse_manager = SSEManager()