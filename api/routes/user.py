from fastapi import APIRouter,Depends,HTTPException,BackgroundTasks
from api.schemas.user import UserRoleUpdateSchema,AddUserSchema,UpdateUserSchema
from operations.crud.user_crud import UserCrud,UserRoles
from database.configs.pg_config import get_pg_db_session
from api.dependencies.token_verification import verify_user
from services.email_service import send_email
from templates.email.accepted import get_login_credential_email_content
from icecream import ic
import os
from dotenv import load_dotenv
from secrets import token_urlsafe
load_dotenv()

router=APIRouter(
    tags=['User Crud']
)

FRONTEND_URL=os.getenv("FRONTEND_URL")

@router.post('/user')
async def add_user(data:AddUserSchema,bgt:BackgroundTasks,user:dict=Depends(verify_user),session=Depends(get_pg_db_session)):
    try:
        password=token_urlsafe(32)
        user=await UserCrud(session=session).add(
            user_role_tocheck=user['role'],
            name=data.name,
            email=data.email,
            role=data.role,
            password=password
        )

        email_content=get_login_credential_email_content(user_name=data.name,user_email=data.email,user_role=data.role,password=password,dashboard_link=FRONTEND_URL)

        bgt.add_task(
            send_email,
            reciver_emails=[data.email],
            subject="Welcome To Tibos CRM — Here Are Your Login Details",
            is_html=True,
            body=email_content
            
        )

        return user
    
    except HTTPException:
        raise

    except Exception as e:
        ic(f"Something went wrong while adding user {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Something went wrong while adding user {e}"
        )

@router.post('/user/email')
async def send_user_email(data:AddUserSchema,bgt:BackgroundTasks,user:dict=Depends(verify_user),session=Depends(get_pg_db_session)):
    try:
        password=token_urlsafe(32)
        user=await UserCrud(session=session).add(
            user_role_tocheck=user['role'],
            name=data.name,
            email=data.email,
            role=data.role,
            password=password
        )

        email_content=get_login_credential_email_content(user_name=data.name,user_email=data.email,user_role=data.role.value,password=password,dashboard_link=FRONTEND_URL)

        bgt.add_task(
            send_email,
            reciver_emails=[data.email],
            subject="Welcome To Tibos CRM — Here Are Your Login Details",
            is_html=True,
            body=email_content
            
        )

        return user
    
    except HTTPException:
        raise

    except Exception as e:
        ic(f"Something went wrong while adding user {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Something went wrong while adding user {e}"
        )

@router.get('/user')
async def get_users(user:dict=Depends(verify_user),session=Depends(get_pg_db_session)):
    return await UserCrud(session=session).get(user_role=user['role'])

@router.get('/user/{user_id}')
async def get_user_by_id(user_id:str,user:dict=Depends(verify_user),session=Depends(get_pg_db_session)):
    return await UserCrud(session=session).get_by_id(user_role=user['role'],userid_toget=user_id)

@router.get('/user/role/{role}')
async def get_users_by_role(role:UserRoles,session=Depends(get_pg_db_session),user:dict=Depends(verify_user)):
    return await UserCrud(session=session).get_by_role(user_role=user['role'],userrole_toget=role)

@router.patch('/user/role')
async def update_user_role(data:UserRoleUpdateSchema,user:dict=Depends(verify_user),session=Depends(get_pg_db_session)):
    return await UserCrud(session=session).update_role(user_role=user['role'],user_toupdate_id=data.user_id,role_toupdate=data.role)

@router.delete('/user/{user_id}')
async def delete_user(user_id:str,user:dict=Depends(verify_user),session=Depends(get_pg_db_session)):
    return await UserCrud(session=session).delete(user_role=user['role'],userid_toremove=user_id)
