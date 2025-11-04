import aiosmtplib,os,asyncio
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
from pydantic import EmailStr
from icecream import ic
from typing import List
import time,asyncio
from typing import Literal
load_dotenv()

SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT"))
SENDER_EMAIL= os.getenv("SENDER_EMAIL")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")


async def check_email_service_health():
    """A simple health check function to verify email service connectivity."""
    try:
        ic(f"🔃 Performing email service health check... as a credentials of {SMTP_SERVER} {SMTP_PORT} {SENDER_EMAIL} {EMAIL_PASSWORD}")
        if SMTP_PORT==465:
            server=aiosmtplib.SMTP(hostname=SMTP_SERVER,port=SMTP_PORT,use_tls=True)
        else:
            server=aiosmtplib.SMTP(hostname=SMTP_SERVER, port=SMTP_PORT, start_tls=True)

        async with server:
            await server.login(SENDER_EMAIL,EMAIL_PASSWORD)
            await server.quit()
        ic("✅ Email service is ready to send emails")
        return True
    
    except Exception as e:
        ic(f"❌ Email service health check failed: {e}")
        return False

async def send_email(reciver_emails:List[EmailStr], subject:str, body:str,is_html:bool=False):
    """on this send_email function, you can send a email either plain or html content"""
    async def send(subtype:Literal['plain','html'],reciver_email:EmailStr):
        try:
            if SMTP_PORT==465:
                server=aiosmtplib.SMTP(hostname=SMTP_SERVER,port=SMTP_PORT,use_tls=True)
            else:
                server=aiosmtplib.SMTP(hostname=SMTP_SERVER, port=SMTP_PORT, start_tls=True)
            
            message=MIMEMultipart()
            message['Subject']=subject
            message['From']=SENDER_EMAIL
            message['To']=reciver_email
            message.attach(MIMEText(body,subtype))
            
            async with server:
                await server.login(SENDER_EMAIL,EMAIL_PASSWORD)
                ic(f"🔃 Sending email to {reciver_email}... ")
                await server.send_message(message)
                ic(f"✅ {reciver_email} - Email sent successfully .")
                await server.quit()
                return f"✅ {reciver_email} - Email sent successfully ."
            
        except Exception as e:
            ic(f"❌ {reciver_email} - Failed to send email: {e}")
            return f"❌ {reciver_email} - Failed to send email: {e}"

    try:
        st=time.time()
        ic("strarting time : ",st)
        subtype='plain'
        if is_html:
            subtype='html'
            
        tasks=[
            asyncio.create_task(send(subtype=subtype,reciver_email=reciver_email))
            for reciver_email in reciver_emails
        ]
        results=await asyncio.gather(*tasks)
        ic(results)
        ic("Total time taken to send emails: ", time.time() - st)

    except Exception as e:
        ic(f"❌ Failed to send email: {e}")

    
    


async def send_email_unoptimized(reciver_emails:List[EmailStr], subject:str, body:str,is_html:bool=False):
    """on this send_email function, you can send a email either plain or html content"""
    try:
        st=time.time()
        ic("strarting time : ",st)
        for receiver_email in reciver_emails:
            ic(f"🔃 Sending email to {receiver_email}... ")
            subtype='plain'
            if is_html:
                subtype='html'

            message=MIMEMultipart()
            message['Subject']=subject
            message['From']=SENDER_EMAIL
            message['To']=receiver_email
            message.attach(MIMEText(body,subtype))

            if SMTP_PORT==465:
                server=aiosmtplib.SMTP(hostname=SMTP_SERVER,port=SMTP_PORT,use_tls=True)
            else:
                server=aiosmtplib.SMTP(hostname=SMTP_SERVER, port=SMTP_PORT, start_tls=True)

            async with server:
                await server.login(SENDER_EMAIL,EMAIL_PASSWORD)
                await server.send_message(message)
                ic("✅ Email sent successfully.")
                await server.quit()
        ic("Total time taken to send emails: ", time.time() - st)
    
    except Exception as e:
        ic(f"❌ Failed to send email: {e}")


if __name__=="__main__":
    asyncio.run(send_email(
        reciver_emails=['aarthig0707@gmail.com','siva967763@gmail.com'],
        subject="This is From Tibos Crm",
        body="<h1>This is a testing message from tibos crm , so dont panic ! 😂 Unoptimized</h1>",
        is_html=True
    ))