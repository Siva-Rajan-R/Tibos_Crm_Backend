import asyncio
from typing import List
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pydantic import EmailStr
import aiosmtplib
from icecream import ic

from infras.caching.models.auth_model import unlink_auth_forgot
from core.settings import SETTINGS


SMTP_SERVER = SETTINGS.SMTP_SERVER
SMTP_PORT = int(SETTINGS.SMTP_PORT)
SENDER_EMAIL = SETTINGS.SENDER_EMAIL
EMAIL_PASSWORD = SETTINGS.EMAIL_PASSWORD


async def send_email(
    client_ip: str,
    reciver_emails: List[EmailStr],
    subject: str,
    body: str,
    is_html: bool = False,
):
    message = MIMEMultipart()
    message["From"] = SENDER_EMAIL
    message["To"] = ", ".join(reciver_emails)
    message["Subject"] = subject

    content_type = "html" if is_html else "plain"
    message.attach(MIMEText(body, content_type))

    try:
        await aiosmtplib.send(
            message,
            hostname=SMTP_SERVER,
            port=SMTP_PORT,
            start_tls=True,
            username=SENDER_EMAIL,
            password=EMAIL_PASSWORD,
            timeout=30,
        )

        ic("Email sent successfully")
        return True

    except Exception as e:
        ic("Error sending email:", e)
        await unlink_auth_forgot(ip=client_ip)
        return False


# ------------------- TEST -------------------
if __name__ == "__main__":
    asyncio.run(
        send_email(
            client_ip="127.0.0.1",
            reciver_emails=[
                "aarthig0707@gmail.com",
                "siva967763@gmail.com"
            ],
            subject="This is From Tibos CRM",
            body="<h1>Testing Gmail SMTP 🚀</h1><p>No panic 😂</p>",
            is_html=True,
        )
    )
