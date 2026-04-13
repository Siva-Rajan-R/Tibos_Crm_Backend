import asyncio,requests
from typing import List,Optional
from pydantic import EmailStr

tenant_id = '5306f651-8fb6-47ee-8b65-2685aadbc3c0'
client_id = '6637f71f-ee8c-4e55-a168-811ebc807a63'
client_secret = 'KYh8Q~vhca6400Bsu00j9n1Sq8N~SVtrU-vhBb2U'
sender_email = 'nithish@tibos.in'

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
<meta name="viewport" content="width=device-width">
<title>TIBOS – Share Your Feedback</title>
</head>

<body style="margin:0;padding:0;background:#ffffff;font-family:Arial,Helvetica,sans-serif;">

<!-- PREHEADER -->

<div style="display:none;font-size:1px;color:#f5f2f2;line-height:1px;max-height:0;max-width:0;opacity:0;overflow:hidden;">
Share your experience with TIBOS and help us improve.
</div>

<table width="100%" cellpadding="0" cellspacing="0" bgcolor="#f5f2f2" border-raduosihfoi>
<tr>
<td align="center" style="padding:30px 10px;">

<table width="600" cellpadding="0" cellspacing="0" bgcolor="#ffffff" style="border:1px solid #E6EEF5;">

<!-- HEADER -->

<tr>
<td style="padding:20px; border-bottom:1px solid #eeeeee;">
<table width="100%">
<tr>

<!-- LOGO -->

<td align="left">
<img src="https://tibosstaticassets.blob.core.windows.net/tibossiteassets/TIBOS_WEB/Logo/tibos%20logo.png" width="110" style="display:block;">
</td>

<!-- SOCIAL ICONS WITH GLASS EFFECT -->

<td align="right">
<table cellpadding="0" cellspacing="0">
<tr>

<!-- Instagram -->

<td style="padding-left:10px;">
<table cellpadding="0" cellspacing="0" style="background:#ffffff;border:1px solid #E6EEF5;border-radius:20px;">
<tr>
<td style="padding:6px;">
<a href="https://www.instagram.com/tibossolutions_official?igsh=c2h0bDd3bjExb2J6">
<img src="https://cdn-icons-png.flaticon.com/512/2111/2111463.png" width="16" style="display:block;border:0;">
</a>
</td>
</tr>
</table>
</td>

<!-- Facebook -->

<td style="padding-left:10px;">
<table cellpadding="0" cellspacing="0" style="background:#ffffff;border:1px solid #E6EEF5;border-radius:20px;">
<tr>
<td style="padding:6px;">
<a href="https://www.facebook.com/share/1BcFGtnMnc/">
<img src="https://cdn-icons-png.flaticon.com/512/733/733547.png" width="16" style="display:block;border:0;">
</a>
</td>
</tr>
</table>
</td>

<!-- LinkedIn -->

<td style="padding-left:10px;">
<table cellpadding="0" cellspacing="0" style="background:#ffffff;border:1px solid #E6EEF5;border-radius:20px;">
<tr>
<td style="padding:6px;">
<a href="https://www.linkedin.com/company/tibos-solutions-and-services-private-limited/">
<img src="https://cdn-icons-png.flaticon.com/512/3536/3536505.png" width="16" style="display:block;border:0;">
</a>
</td>
</tr>
</table>
</td>

</tr>
</table>
</td>

</tr>
</table>
</td>
</tr>

<!-- HERO -->

<tr>
<td align="center" style="padding:30px 20px;">
<span style="font-size:24px;font-weight:bold;color:#003A5C;">
We Value Your Feedback 💙
</span>
<br><br>
<span style="font-size:14px;color:#666;line-height:1.6;">
At <b>TIBOS Solutions & Services</b>, your feedback helps us improve and serve you better.
</span>
</td>
</tr>

<!-- CARDS -->

<tr>
<td style="padding:20px;">
<table width="100%">

<tr>

<td width="50%" valign="top" style="padding:5px;">
<table width="100%" bgcolor="#F3FAFF" style="border-left:4px solid #0B6E99;">
<tr>
<td style="padding:15px;">
<b>Improve Services</b><br>
<span style="font-size:13px;color:#555;">Enhance experience and delivery.</span>
</td>
</tr>
</table>
</td>

<td width="50%" valign="top" style="padding:5px;">
<table width="100%" bgcolor="#FFF6F0" style="border-left:4px solid #FF7A00;">
<tr>
<td style="padding:15px;">
<b>Build Trust</b><br>
<span style="font-size:13px;color:#555;">Help others know our services.</span>
</td>
</tr>
</table>
</td>

</tr>

<tr>

<td width="50%" valign="top" style="padding:5px;">
<table width="100%" bgcolor="#F2FFF8" style="border-left:4px solid #00A86B;">
<tr>
<td style="padding:15px;">
<b>Drive Innovation</b><br>
<span style="font-size:13px;color:#555;">Support continuous improvement.</span>
</td>
</tr>
</table>
</td>

<td width="50%" valign="top" style="padding:5px;">
<table width="100%" bgcolor="#F6F3FF" style="border-left:4px solid #6A5ACD;">
<tr>
<td style="padding:15px;">
<b>Partnership</b><br>
<span style="font-size:13px;color:#555;">Build long-term relationships.</span>
</td>
</tr>
</table>
</td>

</tr>

</table>
</td>
</tr>

<!-- CTA BUTTON -->

<tr>
<td align="center" style="padding:30px;">
<table cellpadding="0" cellspacing="0">
<tr>
<td bgcolor="#0B6E99" style="padding:14px 30px;">
<a href="https://g.page/r/CYrMe3Ssb3X6EBE/review" 
style="color:#ffffff;text-decoration:none;font-weight:bold;font-size:15px;">
⭐ Leave a Google Review
</a>
</td>
</tr>
</table>
</td>
</tr>

<!-- FOOTER -->

<tr>
<td bgcolor="#003A5C" align="center" style="padding:25px;color:#BFDFF2;font-size:12px;">
<b style="color:#ffffff;">TIBOS Solutions & Services Private Limited</b>
<br><br>
Delivering Reliable IT & Digital Solutions
<br>
© 2024 TIBOS. All rights reserved.
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
            sender_email_id="",
            client_ip="127.0.0.1",
            reciver_emails=[
                # "venkat@tibos.in",
                "tibosss-all@tibos.in"
                
            ],
            subject="This is From Tibos CRM",
            body=email_conten,
            is_html=True,
            tenant_id=tenant_id,
            client_id=client_id,
            client_secret=client_secret,
            sender_email="nithish@tibos.in"
        )
    )