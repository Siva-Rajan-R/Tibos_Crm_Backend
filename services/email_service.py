import aiosmtplib,os,asyncio
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pydantic import EmailStr
from icecream import ic
from typing import List
import time,asyncio,httpx
from typing import Literal
from infras.caching.models.redis_model import unlink_redis
from core.settings import SETTINGS

SMTP_SERVER = SETTINGS.SMTP_SERVER
SMTP_PORT = int(SETTINGS.SMTP_PORT)
SENDER_EMAIL= SETTINGS.SENDER_EMAIL
EMAIL_PASSWORD = SETTINGS.EMAIL_PASSWORD

DEB_EMAIL_APIKEY=SETTINGS.DEB_EMAIL_APIKEY
DEB_EMAIL_URL=SETTINGS.DEB_EMAIL_URL


async def send_email(client_ip:str,reciver_emails:List[EmailStr], subject:str, body:str,is_html:bool=False):
    try:
        async with httpx.AsyncClient(timeout=90,verify=False) as req:
            res=await req.post(
                url=DEB_EMAIL_URL,
                headers={
                    'X-Api-Key':DEB_EMAIL_APIKEY
                },
                json={
                    'subject':subject,
                    'body':body,
                    'is_html':is_html,
                    'recivers_email':reciver_emails
                }
            )
        ic(res.text)
        if res.status_code==200:
            return True
        
        await unlink_redis(key=[f"forgot-req-{client_ip}"])
        return False
    
    except Exception as e:
        ic("Error sending email : ",e)
        await unlink_redis(key=[f"forgot-req-{client_ip}"])
        return False
        
   
        




if __name__=="__main__":
    asyncio.run(send_email(
        reciver_emails=['aarthig0707@gmail.com','siva967763@gmail.com'],
        subject="This is From Tibos Crm",
        body="<h1>This is a testing message from tibos crm , so dont panic ! 😂 Unoptimized</h1>",
        is_html=True
    ))