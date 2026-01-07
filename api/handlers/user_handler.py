from infras.primary_db.services.user_service import UserService
from sqlalchemy import select,update,delete,and_,or_,func
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import EmailStr
from core.utils.uuid_generator import generate_uuid
from security.jwt_token import generate_jwt_token,ACCESS_JWT_KEY,REFRESH_JWT_KEY,JWT_ALG
from icecream import ic
from core.data_formats.enums.common_enums import UserRoles
import os,json
from schemas.db_schemas.user import AddUserDbSchema,UpdateUserDbSchema
from schemas.request_schemas.user import AddUserSchema,UpdateUserSchema
from schemas.request_schemas.auth import AuthForgotAcceptSchema,AuthForgotEmailSchema,AuthSchema
from typing import Optional
from security.data_hashing import verfiy_hashed,hash_data
from core.decorators.error_handler_dec import catch_errors
from secrets import token_urlsafe
from . import HTTPException,BaseResponseTypDict,ErrorResponseTypDict,SuccessResponseTypDict

DEFAULT_SUPERADMIN_INFO=json.loads(os.getenv('DEFAULT_SUPERADMIN_INFO'))
 
 
class HandleUserRequest:
    def __init__(self,session:AsyncSession,user_role:UserRoles):
        self.session=session
        self.user_role=user_role

        if self.user_role==UserRoles.SUPER_ADMIN.value:
            return None


    @catch_errors
    async def add(self,data:AddUserSchema):
        return await UserService(session=self.session,user_role=self.user_role).add(data=data)  
        
    
    @catch_errors
    async def update(self,data:UpdateUserDbSchema):
        return await UserService(session=self.session,user_role=self.user_role).update(data=data)
        

    @catch_errors
    async def update_role(self,user_toupdate_id:str,role_toupdate:UserRoles):    
        return await UserService(session=self.session,user_role=self.user_role).update_role(user_toupdate_id=user_toupdate_id,role_toupdate=role_toupdate)
    

    @catch_errors
    async def update_password(self,user_toupdate_id:str,data:AuthForgotAcceptSchema):
        if data.new_password!=data.confirm_password:
            raise HTTPException(
                status_code=400,
                detail=ErrorResponseTypDict(
                    msg="Error : Resteing Password",
                    description="Misstmatch of new and confirm password",
                    status_code=400,
                    success=False
                )
            )
        
        res=await UserService(session=self.session,user_role=self.user_role).update_password(user_toupdate_id=user_toupdate_id,new_password=data.confirm_password)
        if not res:
            raise HTTPException(
                status_code=404,
                detail=ErrorResponseTypDict(
                    status_code=404,
                    success=False,
                    msg="Error : Resetting password",
                    description="Invalid User id"
                )
            )
        
        return SuccessResponseTypDict(
            detail=BaseResponseTypDict(
                status_code=200,
                msg="Password reseted successfully",
                success=True
            )
        )
    
    @catch_errors
    async def delete(self,userid_toremove:str):      
        return await UserService(session=self.session,user_role=self.user_role).delete(userid_toremove=userid_toremove)
        
    
    @catch_errors
    async def get(self):   
        return await UserService(session=self.session,user_role=self.user_role).get()
    
    @catch_errors
    async def get_by_id(self,userid_toget:str):  
        return await UserService(session=self.session,user_role=self.user_role).get_by_id(userid_toget=userid_toget)
    
    @catch_errors
    async def get_by_role(self,userrole_toget:UserRoles):    
        return await UserService(session=self.session,user_role=self.user_role).get_by_role(userrole_toget=userrole_toget)
    

    

    async def search():
        """this is just for abstract this method doesnot do anything"""
        pass