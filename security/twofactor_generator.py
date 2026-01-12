import pyotp
import base64
import qrcode
import secrets
from io import BytesIO
from icecream import ic


def generate_2factor_secret():
    secret=base64.b32encode(secrets.token_urlsafe(32).encode())
    return secret.decode()


def generate_2factor_qr(secret:str,user_name:str,issuer_name:str):
    totp=pyotp.TOTP(s=secret,digits=6,interval=30)
    otp=totp.now()
    ic(otp)
    otp_uri=totp.provisioning_uri(name=user_name,issuer_name=issuer_name)
    qr=qrcode.make(otp_uri)
    buffer=BytesIO()
    qr.save(buffer,format='PNG')
    buffer.seek(0)

    return buffer


def verify_2factor(otp:str,secret:str):
    totp=pyotp.TOTP(s=secret,digits=6,interval=30)
    return totp.verify(otp=otp)


if __name__=="__main__":
    s='NR5GWMSXLJKVG2CXKNUUINKDIJ4G2ZTVM5IHSSKWNBLGIM2XIR4VS3BUOREHUYTEPBWGG==='

    ic(generate_2factor_qr(secret=s,user_name="Siva Rajan R",issuer_name="Tibos-Crm"))
    
    ic(verify_2factor(secret=s,otp='271288'))

