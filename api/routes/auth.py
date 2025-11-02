from fastapi import APIRouter,Depends,HTTPException
from fastapi.responses import RedirectResponse
from api.schemas.auth import UserRoleUpdateSchema,EmailStr
from crud.auth_crud import AuthCrud,UserRoles,generate_jwt_token,ACCESS_JWT_KEY,JWT_ALG
from api.dependencies.token_verification import verify_user
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
AUTHCRUD_OBJ=AuthCrud()


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


@router.get('/auth/token/new')
async def get_new_access_token(user:dict=Depends(verify_user)):
    return {'access_token':generate_jwt_token(
        data={'data':{'email':user['email'],'role':user['role']}},
        secret=ACCESS_JWT_KEY,
        alg=JWT_ALG,
        exp_day=7
    )}

@router.get('/user')
async def get_users(user:dict=Depends(verify_user)):
    return AUTHCRUD_OBJ.get(user_role=user['role'])

@router.get('/user/{email}')
async def get_user_by_email(email:EmailStr,user:dict=Depends(verify_user)):
    return AUTHCRUD_OBJ.get_by_email(email_toget=email,user_role=user['role'])

@router.put('/user/role')
async def update_user_role(data:UserRoleUpdateSchema,user:dict=Depends(verify_user)):
    return AUTHCRUD_OBJ.update_role(user_role=user['role'],email_toupdate=data.email,role_toupdate=data.role)

@router.delete('/user/{email}')
async def delete_user(email:EmailStr,user:dict=Depends(verify_user)):
    return AUTHCRUD_OBJ.delete(user_role=user['role'],email_toremove=email)
