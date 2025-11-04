from fastapi import APIRouter,Depends,HTTPException,Request,BackgroundTasks
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from api.schemas.auth import UserRoleUpdateSchema,EmailStr
from services.email_service import send_email
from templates.email.user_accept import get_user_accept_email_content
from templates.email.accepted import get_accepted_email_content
from crud.auth_crud import AuthCrud,UserRoles,generate_jwt_token,ACCESS_JWT_KEY,REFRESH_JWT_KEY,JWT_ALG
from api.dependencies.token_verification import verify_user
from utils.uuid_generator import generate_uuid
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

template=Jinja2Templates("templates/site")

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
async def auth_redirect(code:str,request:Request,bgt:BackgroundTasks):
    async with httpx.AsyncClient() as client:
        response=await client.post(
            url="https://deb-auth-api.onrender.com/auth/authenticated-user",
            json={'code':code,'client_secret':DEB_AUTH_CLIENT_SECRET}
        )

        if response.status_code!=200:
            raise HTTPException(
                status_code=response.status_code,
                detail=response.text
            )
        
        decoded_token=jwt_token.decode(response.json()['token'],options={'verify_signature':False})
        ic(decoded_token)
        user_data=AUTHCRUD_OBJ.check_email_isexists(email=decoded_token['email'])
        if not user_data:
            auth_id=generate_uuid(data="Authentication id")
            TEMP_DATA[auth_id]=decoded_token
            # confirmation email to super admin
            email_content=get_user_accept_email_content(
                user_name=decoded_token['name'],
                user_email=decoded_token['email'],
                user_role=UserRoles.USER.value,
                accept_link=str(request.base_url)+f'auth/accept/{auth_id}',
                profile_pic_link=decoded_token['profile_picture']
            )

            bgt.add_task(
                send_email,
                reciver_emails=AUTHCRUD_OBJ.get_by_role(role_toget=UserRoles.SUPER_ADMIN),
                subject="User Registeration Accept",
                is_html=True,
                body=email_content
            )
            
            ic('Authentication successfull waiting for confirmation')
            return {
                'msg':'Authentication successfull waiting for confirmation'
            }
        access_token=generate_jwt_token(data={'data':{'email':decoded_token['email'],'role':user_data['role']}},secret=ACCESS_JWT_KEY,alg=JWT_ALG,exp_min=15)
        refresh_token=generate_jwt_token(data={'data':{'email':decoded_token['email'],'role':user_data['role']}},secret=REFRESH_JWT_KEY,alg=JWT_ALG,exp_day=7)
        ic(f"Auth tokens : {access_token} {refresh_token}")
        
        return RedirectResponse(
            url="http://127.0.0.1:8000/",
            status_code=307,
            headers={
                'X-Access-Token':access_token,
                'X-Refresh-Token':refresh_token
            }
        )

@router.get('/auth/accept/{auth_id}')
async def accept_authenticated_user(auth_id:str,request:Request,bgt:BackgroundTasks):
    if TEMP_DATA.get(auth_id) is None:
        raise HTTPException(
            status_code=404,
            detail="Authentication request not found"
        )
    
    auth_tokens=AuthCrud().add_update(
        email=TEMP_DATA[auth_id]['email'],
        name=TEMP_DATA[auth_id]['name'],
        role=UserRoles.USER
    )
    ic(f"Auth tokens : {auth_tokens}")
    email_content=get_accepted_email_content(
        user_name=TEMP_DATA[auth_id]['name'],
        user_email=TEMP_DATA[auth_id]['email'],
        user_role=UserRoles.USER.value,
        dashboard_link='http://127.0.0.1:8000/',
        profile_pic_link=TEMP_DATA[auth_id]['profile_picture']
    )
    bgt.add_task(
        send_email,
        reciver_emails=[TEMP_DATA[auth_id]['email']],
        subject="Your Registration Accepted",
        is_html=True,
        body=email_content
    )

    return template.TemplateResponse(
        'user_accepted.html',
        context={
            'request':request,
            'name':TEMP_DATA[auth_id]['name'],
            'email':TEMP_DATA[auth_id]['email'],
            'role':UserRoles.USER.value,
            'details_link':'http://127.0.0.1:8000/',
            'profile_pic_link':TEMP_DATA[auth_id]['profile_picture']
        }
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

@router.get('/user/role/{role}')
async def get_users_by_role(role:UserRoles):
    return AUTHCRUD_OBJ.get_by_role(role_toget=role)

@router.put('/user/role')
async def update_user_role(data:UserRoleUpdateSchema,user:dict=Depends(verify_user)):
    return AUTHCRUD_OBJ.update_role(user_role=user['role'],email_toupdate=data.email,role_toupdate=data.role)

@router.delete('/user/{email}')
async def delete_user(email:EmailStr,user:dict=Depends(verify_user)):
    return AUTHCRUD_OBJ.delete(user_role=user['role'],email_toremove=email)
