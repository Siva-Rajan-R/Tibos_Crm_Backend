from pydantic import BaseModel,EmailStr


class AuthSchema(BaseModel):
    email:EmailStr
    password:str

class AuthForgotEmailSchema(BaseModel):
    user_email:EmailStr

class AuthForgotAcceptSchema(BaseModel):
    auth_id:str
    new_password:str
    confirm_password:str