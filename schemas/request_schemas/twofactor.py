from pydantic import BaseModel


class TwoFactorOtpSchema(BaseModel):
    tf_otp:str