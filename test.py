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
    <!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>Share Your Feedback - TIBOS</title>
</head>

<body style="margin:0;padding:0;background:#f5f6fa;font-family:Arial, Helvetica, sans-serif;">

<table width="100%" cellpadding="0" cellspacing="0" bgcolor="#f5f6fa">
<tr>
<td align="center">

<table width="620" cellpadding="0" cellspacing="0" bgcolor="#ffffff" style="border:1px solid #e5e7eb;">

<!-- LOGO -->
<tr>
<td align="center" style="padding:25px;border-bottom:3px solid #0B6E99;">
<img src="https://tibosstaticassets.blob.core.windows.net/tibossiteassets/TIBOS_WEB/Logo/tibos%20logo.png" width="170" style="display:block;border:0;">
</td>
</tr>

<!-- HEADER -->
<tr>
<td align="center" style="padding:25px 30px 10px 30px;font-size:22px;font-weight:bold;color:#111;">
Your Feedback Matters to Us
</td>
</tr>

<!-- CONTENT -->
<tr>
<td style="padding:0 30px 20px 30px;font-size:14px;color:#333;line-height:1.7;">

At <strong>TIBOS Solutions & Services Private Limited</strong>, we are committed to delivering reliable IT solutions, digital services, and business support tailored to your needs.

Your review helps us improve, grow, and serve you better.

</td>
</tr>

<!-- VALUE POINTS -->
<tr>
<td style="padding:0 30px 20px 30px;">
<table width="100%" cellpadding="0" cellspacing="0">
<tr>
<td style="font-size:14px;color:#333;line-height:1.7;">

<strong>Your review helps:</strong>

<ul style="padding-left:18px;margin:10px 0;">
<li>Improve our services and customer experience</li>
<li>Help others understand our solutions</li>
<li>Build trust and transparency</li>
<li>Support our continuous innovation</li>
<li>Strengthen long-term partnerships</li>
</ul>

</td>
</tr>
</table>
</td>
</tr>

<!-- REVIEW BOX -->
<tr>
<td style="padding:0 30px 25px 30px;">
<table width="100%" cellpadding="0" cellspacing="0" bgcolor="#f4f6fb">
<tr>
<td align="center" style="padding:25px;border-left:4px solid #0B6E99;">

<div style="font-size:16px;color:#111;font-weight:bold;margin-bottom:10px;">
Share Your Experience With Us
</div>

<div style="font-size:14px;color:#555;margin-bottom:20px;">
It only takes a minute to leave your review
</div>

<a href="https://g.page/r/CYrMe3Ssb3X6EBE/review"
style="background:#0B6E99;color:#ffffff;text-decoration:none;padding:12px 22px;display:inline-block;font-size:14px;font-weight:bold;">
Leave a Review
</a>

<br><br>

<a href="https://g.page/r/CYrMe3Ssb3X6EBE/review" style="color:#0B6E99;font-size:12px;">
https://g.page/r/CYrMe3Ssb3X6EBE/review
</a>

</td>
</tr>
</table>
</td>
</tr>

<!-- FOOTER -->
<tr>
<td align="center" style="padding:20px;font-size:12px;color:#888;border-top:1px solid #eee;">
© TIBOS Solutions & Services Private Limited  
<br>
Delivering Reliable IT & Digital Solutions
</td>
</tr>

</table>

</td>
</tr>
</table>

</body>
</html>
    """
    asyncio.run(
        send_email(
            sender_email_id="siva@tibos.in",
            client_ip="127.0.0.1",
            reciver_emails=[
                "nithish@tibos.in"
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

