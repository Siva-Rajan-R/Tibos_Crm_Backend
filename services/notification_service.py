from sse_starlette.sse import EventSourceResponse
from datetime import datetime,timezone
from asyncio import Queue


notification_queue=Queue()

async def notification_generator():
    print(id(notification_queue))
    while True:
        datas=await notification_queue.get()
        yield {'event':'notification','data':datas}