import smtplib,os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
from pydantic import EmailStr
load_dotenv()

SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT"))
SENDER_EMAIL= os.getenv("SENDER_EMAIL")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")


def send_email(receiver_email:EmailStr, subject:str, body:str,is_html:bool=False):
    """on this send_email function, you can send a email either plain or html content"""
    try:
        print(SMTP_SERVER,SMTP_PORT,SENDER_EMAIL,EMAIL_PASSWORD)
        subtype='plain'
        if is_html:
            subtype='html'

        message=MIMEMultipart()
        message['Subject']=subject
        message['From']=SENDER_EMAIL
        message['To']=receiver_email

        message.attach(MIMEText(body,subtype))

        # Connect to the SMTP server
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(user=SENDER_EMAIL,password=EMAIL_PASSWORD)
            server.send_message(msg=message)
            server.quit()
        
        print("Email sent successfully.")
    
    except Exception as e:
        print(f"Failed to send email: {e}")


if __name__=="__main__":
    send_email(
        receiver_email='siva967763@gmail.com',
        subject="This is From Tibos Crm",
        body="<h1>This is a testing message from tibos crm , so dont panic ! 😂</h1>",
    )