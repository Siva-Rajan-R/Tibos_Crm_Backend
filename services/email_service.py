import asyncio
from typing import List,Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pydantic import EmailStr
import aiosmtplib,requests
from icecream import ic
from infras.primary_db.services.setting_service import SettingsService,SECRET_KEY
from infras.primary_db.main import AsyncLocalSession
from infras.caching.models.auth_model import unlink_auth_forgot
from core.settings import SETTINGS
from schemas.request_schemas.setting import EmailSettingSchema
from core.data_formats.enums.dd_enums import SettingsEnum
from security.symm_encryption import SymmetricEncryption
from core.utils.msgraph_attachments import build_graph_attachments


SMTP_SERVER = SETTINGS.SMTP_SERVER
SMTP_PORT = int(SETTINGS.SMTP_PORT)
SENDER_EMAIL = SETTINGS.SENDER_EMAIL
EMAIL_PASSWORD = SETTINGS.EMAIL_PASSWORD


# async def send_email(
#     client_ip: str,
#     reciver_emails: List[EmailStr],
#     subject: str,
#     body: str,
#     is_html: bool = False,
# ):
#     message = MIMEMultipart()
#     message["From"] = SENDER_EMAIL
#     message["To"] = ", ".join(reciver_emails)
#     message["Subject"] = subject

#     content_type = "html" if is_html else "plain"
#     message.attach(MIMEText(body, content_type))

#     try:
#         await aiosmtplib.send(
#             message,
#             hostname=SMTP_SERVER,
#             port=SMTP_PORT,
#             start_tls=True,
#             username=SENDER_EMAIL,
#             password=EMAIL_PASSWORD,
#             timeout=30,
#         )

#         ic("Email sent successfully")
#         return True

#     except Exception as e:
#         ic("Error sending email:", e)
#         await unlink_auth_forgot(ip=client_ip)
#         return False





def get_graph_token(tenant_id:str,client_id:str,client_secret:str):
    url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"

    data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "scope": "https://graph.microsoft.com/.default",
        "grant_type": "client_credentials",
    }

    res = requests.post(url, data=data)
    res.raise_for_status()
    return res.json()["access_token"]


async def send_email(
    *,
    client_ip: str,
    reciver_emails: List[EmailStr],
    subject: str,
    body: str,
    is_html: bool = False,
    sender_email_id: Optional[str] = None,
    attachments: Optional[List[str]] = None,  # ⭐ NEW
):
    try:
        tenant_id = None
        client_id = None
        client_secret = None
        sender_email = None
        ic(reciver_emails)

        async with AsyncLocalSession() as session:
            emails = (
                await SettingsService(session=session)
                .getby_name(name=SettingsEnum.EMAIL)
            )["settings"][0]
            ic(emails)
            if sender_email_id and sender_email_id in emails['datas']:
                cfg = emails['datas'][sender_email_id]
            else:
                cfg = emails['datas']["order@tibos.in"]
            ic(cfg)
            sender_email = cfg["email"]
            client_id = cfg["client_id"]
            client_secret = SymmetricEncryption(SECRET_KEY).decrypt_data(
                encrypted_data=cfg["client_secret"]
            )
            tenant_id = cfg["tenant_id"]

        token = get_graph_token(
            tenant_id=tenant_id,
            client_id=client_id,
            client_secret=client_secret,
        )

        payload = {
            "message": {
                "subject": subject,
                "body": {
                    "contentType": "HTML" if is_html else "Text",
                    "content": body,
                },
                "toRecipients": [
                    {"emailAddress": {"address": email}}
                    for email in reciver_emails
                ],
            },
            "saveToSentItems": True,
        }

        # 🔥 ATTACHMENT LOGIC
        if attachments:
            payload["message"]["attachments"] = build_graph_attachments(attachments)

        url = f"https://graph.microsoft.com/v1.0/users/{sender_email}/sendMail"

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        res = requests.post(url, headers=headers, json=payload)

        if res.status_code != 202:
            raise Exception(f"Mail failed: {res.status_code} {res.text}")

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
                "siva967763@gmail.com"
            ],
            subject="This is From Tibos CRM",
            body="<h1>Testing Gmail SMTP 🚀</h1><p>No panic 😂</p>",
            is_html=True,
            attachments=['accounts.xlsx']
        )
    )

