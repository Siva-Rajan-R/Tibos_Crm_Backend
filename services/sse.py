import asyncio
from typing import Optional
from icecream import ic
class SSEManager:

    def __init__(self):
        self.connections = {}

    def create(self, client_id):
        ic(client_id)
        q = asyncio.Queue()
        self.connections[client_id] = q
        ic(self.connections)
        return q

    async def send(self, client_id, data):
        ic(client_id,self.connections)
        if client_id in self.connections:
            ic("data => sended => ",data)
            ic(self.connections[client_id])
            await self.connections[client_id].put(data)

    def remove(self, client_id):
        self.connections.pop(client_id, None)


def sse_msg_builder(title:str,description:str,type:str,url:Optional[str]=None):
    return {
        'title':title,
        'description':description,
        'type':type,
        'url':url
    }

sse_manager = SSEManager()