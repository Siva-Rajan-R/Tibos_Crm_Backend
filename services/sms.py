import httpx,os
from dotenv import load_dotenv
from typing import List
from icecream import ic
load_dotenv()
import asyncio


FASTSMS_APIKEY=os.getenv('FASTSMS_APIKEY')

async def send_sms(message:str,numbers:List[int]):
    """on this send sms function you send send any type of message
    which uses a Fast2Sms service
    """

    async with httpx.AsyncClient() as req:
        res=await req.post(
            url="https://www.fast2sms.com/dev/bulkV2",
            headers={
                'authorization': FASTSMS_APIKEY,
                'Content-Type': "application/json",
                'Cache-Control': "no-cache"
            },
            json={
                'message':message,
                'route':'q',
                'numbers':str(numbers)[1:-1]
            }
        )
        
        ic(res.text)
        ic(res.json())

        if not res.json()['return']:
            ic(f"Error sending message {res.json()}")
        else:
            ic("sms sended successfully")

asyncio.run(send_sms("hii hello this from tibos crm",[8248692839]))