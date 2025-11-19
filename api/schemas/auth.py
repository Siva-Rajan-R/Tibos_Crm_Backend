from pydantic import BaseModel,EmailStr


class AuthSchema(BaseModel):
    email:EmailStr
    password:str

class AuthForgotEmailSchema(BaseModel):
    user_email:EmailStr