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


CLIENT_SECRET="fHZ8Q~43KmxPlq2pfD7EcHN0pGncw~QEctrzNb1G"
CLIENT_ID="6637f71f-ee8c-4e55-a168-811ebc807a63"
TENANT_ID="5306f651-8fb6-47ee-8b65-2685aadbc3c0"
SENDER_EMAIL="order@tibos.in"

TOKEN="eyJ0eXAiOiJKV1QiLCJub25jZSI6ImxHU24xZVNxQjRpU1RlQkVnSndZZ1lNVDhIdVhsUHVfa1p2dEVQVjhEelkiLCJhbGciOiJSUzI1NiIsIng1dCI6IlFaZ045SHFOa0dORU00R2VLY3pEMDJQY1Z2NCIsImtpZCI6IlFaZ045SHFOa0dORU00R2VLY3pEMDJQY1Z2NCJ9.eyJhdWQiOiJodHRwczovL2dyYXBoLm1pY3Jvc29mdC5jb20iLCJpc3MiOiJodHRwczovL3N0cy53aW5kb3dzLm5ldC81MzA2ZjY1MS04ZmI2LTQ3ZWUtOGI2NS0yNjg1YWFkYmMzYzAvIiwiaWF0IjoxNzc1MTM0NDQxLCJuYmYiOjE3NzUxMzQ0NDEsImV4cCI6MTc3NTEzODM0MSwiYWlvIjoiazJaZ1lKQlhyYTBWY1UydG12LzUvdVBOMjFKcU5oc2FCWnJmbm10aHNxTnQwOE9FOWZrQSIsImFwcF9kaXNwbGF5bmFtZSI6ImNybSIsImFwcGlkIjoiNjYzN2Y3MWYtZWU4Yy00ZTU1LWExNjgtODExZWJjODA3YTYzIiwiYXBwaWRhY3IiOiIxIiwiaWRwIjoiaHR0cHM6Ly9zdHMud2luZG93cy5uZXQvNTMwNmY2NTEtOGZiNi00N2VlLThiNjUtMjY4NWFhZGJjM2MwLyIsImlkdHlwIjoiYXBwIiwicmgiOiIxLkFWWUFVZllHVTdhUDdrZUxaU2FGcXR2RHdBTUFBQUFBQUFBQXdBQUFBQUFBQUFBQUFBQldBQS4iLCJ0ZW5hbnRfcmVnaW9uX3Njb3BlIjoiQVMiLCJ0aWQiOiI1MzA2ZjY1MS04ZmI2LTQ3ZWUtOGI2NS0yNjg1YWFkYmMzYzAiLCJ1dGkiOiI0eG9ZSVhnbE1VYXpVLTNQbVFRU0FBIiwidmVyIjoiMS4wIiwid2lkcyI6WyIwOTk3YTFkMC0wZDFkLTRhY2ItYjQwOC1kNWNhNzMxMjFlOTAiXSwieG1zX2FjZCI6MTc2MzQ2MTk5OCwieG1zX2FjdF9mY3QiOiIzIDkiLCJ4bXNfZnRkIjoidWttRXRLS1RQd014djBBS3dvZ2lwTVdLVzZ4MHE0U0VROVN0Qk9ueklYVUJhbUZ3WVc1bFlYTjBMV1J6YlhNIiwieG1zX2lkcmVsIjoiMTMgMjAiLCJ4bXNfcGZ0ZXhwIjoxNzc1MjI0NzQxLCJ4bXNfcmQiOiIwLjQyTGxZQkppREJNUzRXQVhFamkwV1ZydXNCZVR4eFNCdUhuVEozdHNGaExoNEJRUzZIcVJGTlBCdHRWX2g4Mkh2TThpOHo4S2lYQndDQWt3TTBEQUFTZ3RKTUxCTFNSUUZ4dllPN3Zoc2RCMDdqbm5yd1Q3TmdJQSIsInhtc19zdWJfZmN0IjoiOSAzIiwieG1zX3RjZHQiOjE2ODA1MDE4MzMsInhtc190bnRfZmN0IjoiMiAzIn0.Z7pynpko94KcFvRvfJBKmAMVv8iXoNnTjNd_wV6ZTiTeuNq79JN5wK1zEt2JqvvU31_KJpZSffgPYOKLeRZhJJSvBD-cc1kdoEs7RguUA528-FLXDD8g-BaaiRIJlI96mS9CE98ts9pILHZBRGQ0xPaqP_P97tLIncyN7rytQgdly5hAE5eALbbNvMUsNoha855wboTRrlRnbSNlQrzIsHwc9LcYwnfi_hEXyNzkcw9XpE6dotiJLRU_IH4uQNL74gL83T5hIh_QFXRaETPBVAq0sWKUijJ5cBp2cbZ6AKaG5NnojaIk0ywaY8euctwXi5yFbIOysnkNKndLcD1PDg"


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
    attachments: Optional[List[str]] = None,
    tenant_id:str,
    client_id:str,
    client_secret:str,
    sender_email:str,
):
    try:
        
        token = get_graph_token(
            tenant_id=tenant_id,
            client_id=client_id,
            client_secret=client_secret,
        )

        ic(token)

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
                ""
            ],
            subject="This is From Tibos CRM",
            body="<h1>Testing Gmail SMTP 🚀</h1><p>No panic 😂</p>",
            is_html=True,
            tenant_id=TENANT_ID,
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            sender_email=SENDER_EMAIL

        )
    )

