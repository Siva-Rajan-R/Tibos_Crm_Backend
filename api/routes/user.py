from fastapi import APIRouter,Depends
from api.schemas.user import UserRoleUpdateSchema
from operations.crud.user_crud import UserCrud,UserRoles
from database.configs.pg_config import get_pg_db_session
from api.dependencies.token_verification import verify_user
from icecream import ic
from dotenv import load_dotenv
load_dotenv()

router=APIRouter(
    tags=['User Crud']
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
