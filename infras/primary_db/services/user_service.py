from ..models.user import UserRoles,Users
from . import BaseServiceModel
from sqlalchemy import select,update,delete,and_,or_,func
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import EmailStr
from core.utils.uuid_generator import generate_uuid
from security.jwt_token import generate_jwt_token,ACCESS_JWT_KEY,REFRESH_JWT_KEY,JWT_ALG
from icecream import ic
import os,json
from schemas.db_schemas.user import AddUserDbSchema,UpdateUserDbSchema
from schemas.request_schemas.user import AddUserSchema,UpdateUserSchema
from ..repos.user_repo import UserRepo
from typing import Optional
from security.data_hashing import verfiy_hashed,hash_data
from core.decorators.error_handler_dec import catch_errors
from secrets import token_urlsafe
from models.response_models.req_res_models import SuccessResponseTypDict,BaseResponseTypDict,ErrorResponseTypDict


DEFAULT_SUPERADMIN_INFO=json.loads(os.getenv('DEFAULT_SUPERADMIN_INFO'))
 
 
class UserService(BaseServiceModel):
    def __init__(self,session:AsyncSession,user_role:UserRoles,cur_user_id:str):
        self.session=session
        self.user_role=user_role
        self.cur_user_id=cur_user_id

    
    @catch_errors
    async def init_superadmin(self):
        ic(f"🔃 Creating Default Super-Admin... {DEFAULT_SUPERADMIN_INFO} {type(DEFAULT_SUPERADMIN_INFO)}")
        for superadmins in DEFAULT_SUPERADMIN_INFO:
            user_obj=UserRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id)
            if (await user_obj.isuser_exists(user_id_email=superadmins['email'])):
                ic("✅ Default Super-Admin Already Exists")
                return
            await UserRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).add(
                data=AddUserDbSchema(
                    id=generate_uuid(),
                    email=superadmins['email'],
                    name=superadmins['name'],
                    role=UserRoles.SUPER_ADMIN,
                    password=hash_data(superadmins['password'])

                ) 
            )
        ic("✅ Default Super-Admin Created Successfully")


    @catch_errors
    async def add(self,data:AddUserSchema):
        user_obj=UserRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id)
        if (await user_obj.isuser_exists(user_id_email=data.email)):
            return ErrorResponseTypDict(status_code=400,success=False,msg="Error : Adding User",description="User with the given email already exists")

        user_id:str=generate_uuid()
        pwd=token_urlsafe(16)
        hashed_pwd=hash_data(data=pwd)
        await UserRepo(session=self.session,user_role=self.user_role,cur_user_id='').add(data=AddUserDbSchema(**data.model_dump(mode='json'),id=user_id,password=hashed_pwd))
        return {'password':pwd}
        
    
    @catch_errors
    async def update(self,data:UpdateUserDbSchema):
        """This is for full update *Name,Role can be changable"""
        data_toupdate=data.model_dump(mode='json',exclude_none=True,exclude_unset=True)
        if not data_toupdate or len(data_toupdate)<1:
            return ErrorResponseTypDict(status_code=400,success=False,msg="Error : Updating User",description="No valid fields to update provided")
        
        return await UserRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).update(data=UpdateUserDbSchema(**data_toupdate))
        

    @catch_errors
    async def update_role(self,user_toupdate_id:str,role_toupdate:UserRoles):    
        return await UserRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).update_role(user_toupdate_id=user_toupdate_id,role_toupdate=role_toupdate)
    
    @catch_errors
    async def update_twofactor(self,user_toupdate_id:str,tf_secret:str):    
        return await UserRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).update_twofactor(user_toupdate_id=user_toupdate_id,tf_secret=tf_secret)

    @catch_errors
    async def update_password(self,user_toupdate_id:str,new_password:str):
        hashed_pwd=hash_data(data=new_password)
        return await UserRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).update_password(user_toupdate_id=user_toupdate_id,new_hashed_password=hashed_pwd)

    @catch_errors
    async def delete(self,userid_toremove:str,soft_delete:bool=True):      
        return await UserRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).delete(userid_toremove=userid_toremove,soft_delete=soft_delete)


    @catch_errors  
    async def recover(self,userid_torecover:str):
        return await UserRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).recover(userid_torecover=userid_torecover)

    @catch_errors
    async def get(self,include_deleted:Optional[bool]=False):   
        return await UserRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).get(include_deleted=include_deleted)
    
    @catch_errors
    async def get_by_id(self,userid_toget:str):  
        return await UserRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).get_by_id(userid_toget=userid_toget)
    
    @catch_errors
    async def get_by_role(self,userrole_toget:UserRoles):    
        return await UserRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).get_by_role(userrole_toget=userrole_toget)
    


    async def search():
        """this is just for abstract this method doesnot do anything"""
        pass