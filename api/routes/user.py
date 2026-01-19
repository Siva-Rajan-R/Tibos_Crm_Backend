from fastapi import APIRouter,Depends,HTTPException,BackgroundTasks,Request,Query
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
from typing import Optional

router=APIRouter(
    tags=['User Crud'],
    prefix='/user'
)

FRONTEND_URL=SETTINGS.FRONTEND_URL

@router.post('')
async def add_user(data:AddUserSchema,request:Request,bgt:BackgroundTasks,user:dict=Depends(verify_user),session=Depends(get_pg_db_session)):
    return await HandleUserRequest(session=session,user_role=user['role'],bgt=bgt,request=request).add(
        data=data
    )
     
@router.put('')
async def update_user(data:UpdateUserSchema,request:Request,bgt:BackgroundTasks,user:dict=Depends(verify_user),session=Depends(get_pg_db_session)):
    user = await HandleUserRequest(session=session,user_role=user['role'],bgt=bgt,request=request).update(data=data)
    return user

@router.get('')
async def get_users(request:Request,bgt:BackgroundTasks,user:dict=Depends(verify_user),session=Depends(get_pg_db_session)):
    return await HandleUserRequest(session=session,user_role=user['role'],bgt=bgt,request=request).get()

@router.get('/{user_id}')
async def get_user_by_id(user_id:str,request:Request,bgt:BackgroundTasks,user:dict=Depends(verify_user),session=Depends(get_pg_db_session)):
    return await HandleUserRequest(session=session,user_role=user['role'],bgt=bgt,request=request).get_by_id(userid_toget=user_id)

@router.get('/role/{role}')
async def get_users_by_role(role:UserRoles,request:Request,bgt:BackgroundTasks,session=Depends(get_pg_db_session),user:dict=Depends(verify_user)):
    return await HandleUserRequest(session=session,user_role=user['role'],bgt=bgt,request=request).get_by_role(userrole_toget=role)

@router.patch('/role')
async def update_user_role(data:UserRoleUpdateSchema,request:Request,bgt:BackgroundTasks,user:dict=Depends(verify_user),session=Depends(get_pg_db_session)):
    user=await HandleUserRequest(session=session,user_role=user['role'],bgt=bgt,request=request).update_role(user_toupdate_id=data.user_id,role_toupdate=data.role)
    return user

@router.delete('/{user_id}')
async def delete_user(user_id:str,request:Request,bgt:BackgroundTasks,soft_delete:Optional[bool]=Query(True),user:dict=Depends(verify_user),session=Depends(get_pg_db_session)):
    user=await HandleUserRequest(session=session,user_role=user['role'],bgt=bgt,request=request).delete(userid_toremove=user_id,soft_delete=soft_delete)
    return user

@router.delete('/recover/{user_id}')
async def recover_user(user_id:str,request:Request,bgt:BackgroundTasks,user:dict=Depends(verify_user),session=Depends(get_pg_db_session)):
    user=await HandleUserRequest(session=session,user_role=user['role'],bgt=bgt,request=request).recover(userid_torecover=user_id)
    return user
