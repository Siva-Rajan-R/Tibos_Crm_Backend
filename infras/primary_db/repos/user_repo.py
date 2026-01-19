from ..models.user import UserRoles,Users
from . import BaseRepoModel
from sqlalchemy import select,update,delete,and_,or_,func
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import EmailStr
from core.utils.uuid_generator import generate_uuid
from security.jwt_token import generate_jwt_token,ACCESS_JWT_KEY,REFRESH_JWT_KEY,JWT_ALG
from . import HTTPException
from icecream import ic
import os,json
from schemas.db_schemas.user import AddUserDbSchema,UpdateUserDbSchema
from typing import Optional
from security.data_hashing import verfiy_hashed,hash_data
from core.decorators.db_session_handler_dec import start_db_transaction
from secrets import token_urlsafe

DEFAULT_SUPERADMIN_INFO=json.loads(os.getenv('DEFAULT_SUPERADMIN_INFO'))
 
 
class UserRepo(BaseRepoModel):
    def __init__(self,session:AsyncSession,user_role:UserRoles):
        self.session=session
        self.user_role=user_role
        self.users_cols=(
            Users.id,
            Users.email,
            Users.name,
            Users.role
        )

    async def isuser_exists(self,user_id_email:str):
        return (await self.session.execute(
            select(
                Users.id,
                Users.email,
                Users.password,
                Users.name,
                Users.role,
                Users.tf_secret

            ).where(or_(Users.email==user_id_email,Users.id==user_id_email))
        )).mappings().one_or_none()


    @start_db_transaction
    async def add(self,data:AddUserDbSchema):      

        self.session.add(Users(**data.model_dump(mode='json')))
        
        return True
    
    @start_db_transaction
    async def update(self,data:UpdateUserDbSchema):
        """This is for full update *Name,Role can be changable"""
        data_toupdate=data.model_dump(mode='json',exclude=['user_id'],exclude_none=True,exclude_unset=True)
        if not data_toupdate or len(data_toupdate)<1:
            return False
        
        username_toupdate=update(
            Users
        ).where(
            Users.id==data.user_id
        ).values(
            **data_toupdate
        ).returning(Users.id)
        is_updated = (await self.session.execute(username_toupdate)).scalar_one_or_none()

        return is_updated
        
    @start_db_transaction
    async def update_role(self,user_toupdate_id:str,role_toupdate:UserRoles):    
        userrole_toupdate=update(Users).where(Users.id==user_toupdate_id).values(
            role=role_toupdate.value
        ).returning(Users.id)

        is_updated=(await self.session.execute(userrole_toupdate)).scalar_one_or_none()
        
        return is_updated
    

    @start_db_transaction
    async def update_password(self,user_toupdate_id:str,new_hashed_password:str):
        userpwd_toupdate=update(Users).where(Users.id==user_toupdate_id).values(
            password=new_hashed_password
        ).returning(Users.id)

        is_updated=(await self.session.execute(userpwd_toupdate)).scalar_one_or_none()
        
        return is_updated
    
    @start_db_transaction
    async def update_twofactor(self,user_toupdate_id:str,tf_secret:str):
        usertf_toupdate=update(Users).where(Users.id==user_toupdate_id).values(
            tf_secret=tf_secret
        ).returning(Users.id)

        is_updated=(await self.session.execute(usertf_toupdate)).scalar_one_or_none()
        
        return is_updated


    @start_db_transaction
    async def delete(self,userid_toremove:str,soft_delete:bool=True):

        if soft_delete:
            user_todelete=update(Users).where(Users.id==userid_toremove,Users.is_deleted==False).values(
                is_deleted=True
            ).returning(Users.id)
            is_deleted=(await self.session.execute(user_todelete)).scalar_one_or_none()
            return is_deleted
        
        else:
            if self.user_role if isinstance(self.user_role,UserRoles) else self.user_role!=UserRoles.SUPER_ADMIN.value:
                return False
            
            user_todelete=delete(Users).where(Users.id==userid_toremove).returning(Users.id)
            is_deleted=(await self.session.execute(user_todelete)).scalar_one_or_none()
            return is_deleted
    
    @start_db_transaction
    async def recover(self,userid_torecover:str):
        if self.user_role.value if isinstance(self.user_role,UserRoles) else self.user_role!=UserRoles.SUPER_ADMIN.value:
            return False
        
        user_torecover=update(Users).where(Users.id==userid_torecover,Users.is_deleted==True).values(
            is_deleted=False
        ).returning(Users.id)
        is_recovered=(await self.session.execute(user_torecover)).scalar_one_or_none()
        return is_recovered
        
    

    async def get(self,include_deleted:bool=False):
        users=(await self.session.execute(
            select(
                *self.users_cols,
                func.date(func.timezone("Asia/Kolkata",Users.created_at)).label("user_created_at")
            ).where(
                Users.is_deleted==include_deleted
            )
        )).mappings().all()

        return {'users':users}
    

    async def get_by_id(self,userid_toget:str):  
        user_toget=select(
            *self.users_cols,
            func.date(func.timezone("Asia/Kolkata",Users.created_at)).label("user_created_at")
        ).where(
            userid_toget==Users.id,
            Users.is_deleted==False
        )

        user=(await self.session.execute(user_toget)).mappings().one_or_none()

        return {'user':user}
    

    async def get_by_role(self,userrole_toget:UserRoles):    
        user_toget=select(
            *self.users_cols,
            func.date(func.timezone("Asia/Kolkata",Users.created_at)).label("user_created_at")
        ).where(
            userrole_toget.value==Users.role,
            Users.is_deleted==False
        )

        user=(await self.session.execute(user_toget)).mappings().all()

        return {'user':user}
    

    

    async def search():
        """this is just for abstract this method doesnot do anything"""
        pass