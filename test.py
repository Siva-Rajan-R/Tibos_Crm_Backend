import asyncio,requests
from typing import List,Optional
from pydantic import EmailStr

tenant_id = '5306f651-8fb6-47ee-8b65-2685aadbc3c0'
client_id = '6637f71f-ee8c-4e55-a168-811ebc807a63'
client_secret = 'KYh8Q~vhca6400Bsu00j9n1Sq8N~SVtrU-vhBb2U'
sender_email = 'siva@tibos.in'

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
    tenant_id = None,
    client_id = None,
    client_secret = None,
    sender_email = None
):
    try:
        

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
        return False





# ------------------- TEST -------------------
if __name__ == "__main__":
    email_conten="""
    <h1>Hello THis is</h1>
    """
    asyncio.run(
        send_email(
            sender_email_id="siva@tibos.in",
            client_ip="127.0.0.1",
            reciver_emails=[
                "siva@tibos.in"
            ],
            subject="This is From Tibos CRM",
            body=email_conten,
            is_html=True,
            tenant_id=tenant_id,
            client_id=client_id,
            client_secret=client_secret,
            sender_email=sender_email
        )
    )

