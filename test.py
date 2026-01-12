import pyotp
from base64 import b32encode
import base64
from secrets import token_urlsafe
import qrcode
from io import BytesIO

s=b32encode(token_urlsafe(32).encode())
print(s)
secret='IRNEMRJVPAZWQSLEGNSTCRCMLFFUQTLKOZ3EYM2TKJQUI3CNKAZEK6SIJUYGYQ2DGVPXO==='

totp=pyotp.TOTP(s=secret,digits=6)
uri=totp.provisioning_uri(name="Siva Rajan R",issuer_name="Tibos-Crm")
print(uri)
print(totp.now())
qr=qrcode.make(uri)
print(qr)
buffer=BytesIO()
qr.save(buffer)
qr_base64 = base64.b64encode(buffer.getvalue()).decode()
print(qr_base64)