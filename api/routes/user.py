from fastapi import APIRouter,Depends,HTTPException,BackgroundTasks,Request
from schemas.request_schemas.user import UserRoleUpdateSchema,AddUserSchema,UpdateUserSchema
from ..handlers.user_handler import HandleUserRequest,UserRoles
from infras.primary_db.main import get_pg_db_session
from api.dependencies.token_verification import verify_user
from services.email_service import send_email
from templates.email.accepted import get_login_credential_email_content
from infras.caching.models.redis_model import unlink_redis
from icecream import ic
import os
from core.settings import SETTINGS
from secrets import token_urlsafe

router=APIRouter(
    tags=['User Crud']
)

FRONTEND_URL=SETTINGS.FRONTEND_URL

@router.post('/user')
async def add_user(data:AddUserSchema,request:Request,bgt:BackgroundTasks,user:dict=Depends(verify_user),session=Depends(get_pg_db_session)):
    user=await HandleUserRequest(session=session,user_role=user['role']).add(
        data=data
    )
    password=user.get('password')
    email_content=get_login_credential_email_content(user_name=data.name,user_email=data.email,user_role=data.role.value,password=password,dashboard_link=FRONTEND_URL)

    bgt.add_task(
        send_email,
        reciver_emails=[data.email],
        subject="Welcome To Tibos CRM — Here Are Your Login Details",
        is_html=True,
        body=email_content,
        client_ip=request.client.host.__str__()
        
    )

    return user
    

# @router.post('/user/email')
# async def send_user_email(data:AddUserSchema,bgt:BackgroundTasks,request:Request,user:dict=Depends(verify_user),session=Depends(get_pg_db_session)):
#     try:
#         password=token_urlsafe(32)
#         user=await HandleUserRequest(session=session).add(
#             user_role_tocheck=user['role'],
#             name=data.name,
#             email=data.email,
#             role=data.role,
#             password=password
#         )

#         email_content=get_login_credential_email_content(user_name=data.name,user_email=data.email,user_role=data.role.value,password=password,dashboard_link=FRONTEND_URL)

#         bgt.add_task(
#             send_email,
#             reciver_emails=[data.email],
#             subject="Welcome To Tibos CRM — Here Are Your Login Details",
#             is_html=True,
#             body=email_content,
#             client_ip=str(request.client.host)
            
#         )

#         return user
    
#     except HTTPException:
#         raise

#     except Exception as e:
#         ic(f"Something went wrong while adding user {e}")
#         raise HTTPException(
#             status_code=500,
#             detail=f"Something went wrong while adding user {e}"
#         )


@router.put('/user')
async def update_user(data:UpdateUserSchema,request:Request,user:dict=Depends(verify_user),session=Depends(get_pg_db_session)):
    user = await HandleUserRequest(session=session,user_role=user['role']).update(data=data)
    await unlink_redis(key=[f"token-verify-{request.client.host}"])
    return user

@router.get('/user')
async def get_users(user:dict=Depends(verify_user),session=Depends(get_pg_db_session)):
    return await HandleUserRequest(session=session,user_role=user['role']).get()

@router.get('/user/{user_id}')
async def get_user_by_id(user_id:str,user:dict=Depends(verify_user),session=Depends(get_pg_db_session)):
    return await HandleUserRequest(session=session,user_role=user['role']).get_by_id(userid_toget=user_id)

@router.get('/user/role/{role}')
async def get_users_by_role(role:UserRoles,session=Depends(get_pg_db_session),user:dict=Depends(verify_user)):
    return await HandleUserRequest(session=session,user_role=user['role']).get_by_role(userrole_toget=role)

@router.patch('/user/role')
async def update_user_role(data:UserRoleUpdateSchema,request:Request,user:dict=Depends(verify_user),session=Depends(get_pg_db_session)):
    user=await HandleUserRequest(session=session,user_role=user['role']).update_role(user_toupdate_id=data.user_id,role_toupdate=data.role)
    await unlink_redis(key=[f"token-verify-{request.client.host}"])
    return user

@router.delete('/user/{user_id}')
async def delete_user(user_id:str,request:Request,user:dict=Depends(verify_user),session=Depends(get_pg_db_session)):
    user=await HandleUserRequest(session=session,user_role=user['role']).delete(userid_toremove=user_id)
    await unlink_redis(key=[f"token-verify-{request.client.host}"])
    return user
