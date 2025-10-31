from fastapi import APIRouter,Depends,HTTPException
from fastapi.responses import RedirectResponse
from pydantic import BaseModel,EmailStr
from crud.auth_crud import AuthCrud,UserRoles
import httpx,os
from configs.pyjwt_config import jwt_token
from icecream import ic
from dotenv import load_dotenv
load_dotenv()

router=APIRouter(
    tags=['Auth Crud']
)

TEMP_DATA={}

DEB_AUTH_APIKEY=os.getenv("DEB_AUTH_APIKEY")
DEB_AUTH_CLIENT_SECRET=os.getenv("DEB_AUTH_CLIENT_SECRET")

class AuthSchema(BaseModel):
    email:EmailStr
    name:str
    role:UserRoles

@router.get('/auth')
async def auth_user():
    async with httpx.AsyncClient() as client:
        response=await client.post(
            url="https://deb-auth-api.onrender.com/auth",
            json={'apikey':DEB_AUTH_APIKEY}
        )
        if response.status_code==200:
            return response.json()
    raise HTTPException(
        status_code=response.status_code,
        detail=response.text
    )
        
@router.get('/auth/redirect')
async def auth_redirect(code:str):
    async with httpx.AsyncClient() as client:
        response=await client.post(
            url="https://deb-auth-api.onrender.com/auth/authenticated-user",
            json={'code':code,'client_secret':DEB_AUTH_CLIENT_SECRET}
        )
        if response.status_code==200:
            decoded_token=jwt_token.decode(response.json()['token'],options={'verify_signature':False})
            ic(decoded_token)
            # instead of adding need to send a confirmation email to super admin
            auth_tokens=AuthCrud().add_update(
                email=decoded_token['email'],
                name=decoded_token['name'],
                role=UserRoles.USER
            )
            ic(f"Auth tokens : {auth_tokens}")
            return RedirectResponse(
                url="http://127.0.0.1:8000/",
                status_code=307,
                headers=auth_tokens
            )
        
    raise HTTPException(
        status_code=response.status_code,
        detail=response.text
    )


@router.get('/user')
async def get_users():
    return AuthCrud().get()

@router.get('/user/{user_email}')
async def get_user_by_email(user_email:EmailStr):
    return AuthCrud().get_by_email(user_email)

@router.delete('/user/{user_email}')
async def delete_user(user_email:EmailStr):
    email="siva967763@gmail.com"
    return AuthCrud().delete(user_email=email,email_toremove=user_email)
