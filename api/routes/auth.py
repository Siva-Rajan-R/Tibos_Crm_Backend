from fastapi import APIRouter,Depends,HTTPException,Request,BackgroundTasks
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from services.email_service import send_email
from templates.email.user_accept import get_user_accept_email_content
from templates.email.accepted import get_login_credential_email_content
from templates.email.forgot import get_forgot_password_email_content,get_password_reset_success_email
from infras.primary_db.repos.auth_repo import AuthRepo
from security.jwt_token import generate_jwt_token,ACCESS_JWT_KEY,REFRESH_JWT_KEY,JWT_ALG
from core.data_formats.enums.common_enums import UserRoles
from api.dependencies.token_verification import verify_user
from core.utils.uuid_generator import generate_uuid
from infras.caching.models.redis_model import get_redis,set_redis,unlink_redis
from infras.primary_db.main import get_pg_db_session
import os
from ..handlers.user_handler import HandleUserRequest
from infras.primary_db.services.user_service import UserService,UserRepo
from schemas.request_schemas.auth import AuthSchema,AuthForgotEmailSchema,AuthForgotAcceptSchema
from security.data_hashing import verfiy_hashed,hash_data
from icecream import ic
from core.settings import SETTINGS

router=APIRouter(
    tags=['Auth Crud'],
    prefix='/auth'
)

DEB_AUTH_APIKEY=SETTINGS.DEB_AUTH_APIKEY
DEB_AUTH_CLIENT_SECRET=SETTINGS.DEB_AUTH_CLIENT_SECRET
FRONTEND_URL=SETTINGS.FRONTEND_URL
AUTHCRUD_OBJ=AuthRepo()

template=Jinja2Templates("templates/site")

@router.post('')
async def auth_user(data:AuthSchema,request:Request,session=Depends(get_pg_db_session)):
    user=(await UserRepo(session=session,user_role='').isuser_exists(user_id_email=data.email))
    if user is None:
        raise HTTPException(
            status_code=401,
            detail="invalid User"
        )
    
    verfiy_hashed(plain_data=data.password,hashed_data=user['password'])
    
    access_token=generate_jwt_token(data={'data':{'email':user['email'],'role':user['role'],'id':user['id']}},secret=ACCESS_JWT_KEY,alg=JWT_ALG,exp_day=7)
    refresh_token=generate_jwt_token(data={'data':{'email':user['email'],'role':user['role'],'id':user['id']}},secret=REFRESH_JWT_KEY,alg=JWT_ALG,exp_day=7)
    ic(f"Auth tokens : {access_token} {refresh_token}")
    return {
        'access_token':access_token,
        'refresh_token':refresh_token,
        'user_name':user['name'],
        'user_role':user['role']
    }


@router.post('/forgot')
async def forgot_password(data:AuthForgotEmailSchema,bgt:BackgroundTasks,request:Request,session=Depends(get_pg_db_session)):
    try:
        forgot_req:str=await get_redis(f"forgot-req-{request.client.host}")
        if forgot_req:
            raise HTTPException(
                status_code=409,
                detail="Already in progress..."
            )
        
        user=(await UserRepo(session=session,user_role='').isuser_exists(user_id_email=data.user_email))
        auth_id:str=generate_uuid("Authenticayion id")
        ic(auth_id)
        if user is None:
            raise HTTPException(
                status_code=401,
                detail="invalid User"
            )

        email_content=get_forgot_password_email_content(
            user_name=user['name'],
            user_email=user['email'],
            reset_link=f"{FRONTEND_URL}/forgot?auth_id={auth_id}"
        )

        bgt.add_task(
            send_email,
            reciver_emails=[user['email']],
            subject="Tibos CRM — Reset Your Password",
            is_html=True,
            body=email_content,
            client_ip=str(request.client.host)
        )

        await set_redis(key=f"forgot-req-{request.client.host}",value=auth_id,expire=1000)
        await set_redis(key=auth_id,value={'ip':request.client.host,'id':user['id'],'email':user['email'],'name':user['name']},expire=1000)

        return "Sending email to user..."
    
    except HTTPException:
        raise

    except Exception as e:
        ic(f"Something went wrong while sending user cred {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Something went wrong while sending user cred {e}"
        )


@router.post('/forgot/accept')
async def accept_new_password(data:AuthForgotAcceptSchema,bgt:BackgroundTasks,request:Request,session=Depends(get_pg_db_session)):
    forgot_req_ip:str=await get_redis(f"forgot-req-{request.client.host}")
    auth_info:dict=await get_redis(data.auth_id)

    await unlink_redis([f"forgot-req-{request.client.host}",data.auth_id])

    if not forgot_req_ip:
        raise HTTPException(
            status_code=403,
            detail="Not requested forgot"
        )
    
    if not auth_info:
        raise HTTPException(
            status_code=404,
            detail="Auth id expired"
        )
    
    if auth_info['ip']!=request.client.host:
        raise HTTPException(
            status_code=401,
            detail="Network interuppted"
        )
    
    
    user=await HandleUserRequest(session=session,user_role=UserRoles.SUPER_ADMIN,bgt=bgt,request=request).update_password(user_toupdate_id=auth_info['id'],data=data)

    email_content=get_password_reset_success_email(
        user_email=auth_info['email'],
        user_name=auth_info['name'],
        dashboard_link=f"{FRONTEND_URL}/login"
    )

    bgt.add_task(
        send_email,
        reciver_emails=[auth_info['email']],
        subject="Tibos Crm — Password Changed Successfully",
        is_html=True,
        body=email_content,
        client_ip=str(request.client.host)
        
    )

    return user
 

@router.get('/token/new')
async def get_new_access_token(user:dict=Depends(verify_user)):
    return {'access_token':generate_jwt_token(
        data={'data':{'email':user['email'],'role':user['role']}},
        secret=ACCESS_JWT_KEY,
        alg=JWT_ALG,
        exp_day=7
    )}

