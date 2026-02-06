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
from schemas.request_schemas.user import AddUserSchema,UpdateUserSchema,RecoverUserSchema,PasswordResetSchema
from schemas.request_schemas.auth import AuthForgotAcceptSchema,AuthForgotEmailSchema,AuthSchema
from typing import Optional
from security.data_hashing import verfiy_hashed,hash_data
from core.decorators.error_handler_dec import catch_errors
from infras.caching.models.redis_model import unlink_redis
from secrets import token_urlsafe
from . import HTTPException,BaseResponseTypDict,ErrorResponseTypDict,SuccessResponseTypDict,BackgroundTasks,Request
from services.email_service import send_email
from templates.email.accepted import get_login_credential_email_content
from core.settings import SETTINGS

DEFAULT_SUPERADMIN_INFO=SETTINGS.DEFAULT_SUPERADMIN_INFO
FRONTEND_URL=SETTINGS.FRONTEND_URL
 
 
class HandleUserRequest:
    def __init__(self,session:AsyncSession,user_role:UserRoles,cur_user_id:str,bgt:BackgroundTasks,request:Request):
        self.session=session
        self.user_role=user_role
        self.bgt=bgt
        self.request=request
        self.cur_user_id=cur_user_id

        # if isinstance(self.user_role,UserRoles):
        #     self.user_role=self.user_role.value

        # if self.user_role!=UserRoles.SUPER_ADMIN.value:
        #     raise HTTPException(
        #         status_code=401,
        #         detail=ErrorResponseTypDict(
        #             msg="Error : ",
        #             description="Insufficient permission",
        #             status_code=401,
        #             success=False
        #         ).model_dump(mode='json')
        #     )


    @catch_errors
    async def add(self,data:AddUserSchema):
        res=await UserService(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).add(data=data)

        if not res or isinstance(res,ErrorResponseTypDict):
            detail:ErrorResponseTypDict=ErrorResponseTypDict(
                    status_code=400,
                    msg="Error : Creating User",
                    description="A Unknown Error, Please Try Again Later!",
                    success=False
                ) if not isinstance(res,ErrorResponseTypDict) else res
            
            raise HTTPException(
                status_code=detail.status_code,
                detail=detail.model_dump(mode='json')
            )
        
        password=res.get('password')
        email_content=get_login_credential_email_content(user_name=data.name,user_email=data.email,user_role=data.role.value,password=password,dashboard_link=FRONTEND_URL)

        self.bgt.add_task(
            send_email,
            reciver_emails=[data.email],
            subject="Welcome To Tibos CRM — Here Are Your Login Details",
            is_html=True,
            body=email_content,
            client_ip=self.request.client.host.__str__()
            
        )

        return SuccessResponseTypDict(
            detail=BaseResponseTypDict(
                status_code=200,
                success=True,
                msg="User created successfully"
            )
        )
        
    
    @catch_errors
    async def update(self,data:UpdateUserSchema):
        res = await UserService(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).update(data=data)
        if not res or isinstance(res,ErrorResponseTypDict):
            detail:ErrorResponseTypDict=ErrorResponseTypDict(
                    status_code=400,
                    msg="Error : Updating User",
                    description="A Unknown Error, Please Try Again Later!",
                    success=False
                ) if not isinstance(res,ErrorResponseTypDict) else res
            
            raise HTTPException(
                status_code=detail.status_code,
                detail=detail.model_dump(mode='json')
            )
        
        await unlink_redis(key=[f"token-verify-{data.user_id}"])
        return SuccessResponseTypDict(
            detail=BaseResponseTypDict(
                status_code=200,
                success=True,
                msg="User updated successfully"
            )
        )
        

    @catch_errors
    async def update_role(self,user_toupdate_id:str,role_toupdate:UserRoles):    
        res=await UserService(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).update_role(user_toupdate_id=user_toupdate_id,role_toupdate=role_toupdate)
        if not res or isinstance(res,ErrorResponseTypDict):
            detail:ErrorResponseTypDict=ErrorResponseTypDict(
                    status_code=400,
                    msg="Error : Updating User Role",
                    description="A Unknown Error, Please Try Again Later!",
                    success=False
                ) if not isinstance(res,ErrorResponseTypDict) else res
            
            raise HTTPException(
                status_code=detail.status_code,
                detail=detail.model_dump(mode='json')
            )
        
        await unlink_redis(key=[f"token-verify-{user_toupdate_id}"])
        return SuccessResponseTypDict(
            detail=BaseResponseTypDict(
                status_code=200,
                success=True,
                msg="User updated successfully"
            )
        )
    

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
        
        if len(data.confirm_password)<7:
            raise HTTPException(
                status_code=400,
                detail=ErrorResponseTypDict(
                    msg="Error : Resteing Password",
                    description="Password length Should be greater than 6",
                    status_code=400,
                    success=False
                )
            )
        
        res=await UserService(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).update_password(user_toupdate_id=user_toupdate_id,new_password=data.confirm_password)
        if not res or isinstance(res,ErrorResponseTypDict):
            detail:ErrorResponseTypDict=ErrorResponseTypDict(
                    status_code=400,
                    msg="Error : Reseting Password",
                    description="A Unknown Error, Please Try Again Later!",
                    success=False
                ) if not isinstance(res,ErrorResponseTypDict) else res
            
            raise HTTPException(
                status_code=detail.status_code,
                detail=detail.model_dump(mode='json')
            )
        
        return SuccessResponseTypDict(
            detail=BaseResponseTypDict(
                status_code=200,
                msg="Password reseted successfully",
                success=True
            )
        )
    
    @catch_errors
    async def delete(self,userid_toremove:str,soft_delete:bool=True):      
        res = await UserService(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).delete(userid_toremove=userid_toremove,soft_delete=soft_delete)
        if not res or isinstance(res,ErrorResponseTypDict):
            detail:ErrorResponseTypDict=ErrorResponseTypDict(
                    status_code=400,
                    msg="Error : Deleting User",
                    description="A Unknown Error, Please Try Again Later!",
                    success=False
                ) if not isinstance(res,ErrorResponseTypDict) else res
            
            raise HTTPException(
                status_code=detail.status_code,
                detail=detail.model_dump(mode='json')
            )
        
        await unlink_redis(key=[f"token-verify-{userid_toremove}"])
        return SuccessResponseTypDict(
            detail=BaseResponseTypDict(
                status_code=200,
                success=True,
                msg="User deleted successfully"
            )
        )
    
    async def reset_pwd(self,data:PasswordResetSchema):
        res=await UserService(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).update_password(user_toupdate_id=data.user_id,new_password=data.new_password)
        if not res or isinstance(res,ErrorResponseTypDict):
            detail:ErrorResponseTypDict=ErrorResponseTypDict(
                    status_code=400,
                    msg="Error : Reseting User Password",
                    description="A Unknown Error, Please Try Again Later!",
                    success=False
                ) if not isinstance(res,ErrorResponseTypDict) else res
            
            raise HTTPException(
                status_code=detail.status_code,
                detail=detail.model_dump(mode='json')
            )
        
        if len(data.new_password)<7:
            raise HTTPException(
                status_code=400,
                detail=ErrorResponseTypDict(
                    msg="Error : Resteing Password",
                    description="Password length Should be greater than 6",
                    status_code=400,
                    success=False
                ).model_dump(mode='json')
            )
        
        return SuccessResponseTypDict(
            detail=BaseResponseTypDict(
                msg="User Password changed successfully",
                success=True,
                status_code=200
            )
        )
    
    @catch_errors
    async def recover(self,data:RecoverUserSchema): 
        res = await UserService(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).recover(userid_torecover=data.user_id)
        if not res or isinstance(res,ErrorResponseTypDict):
            detail:ErrorResponseTypDict=ErrorResponseTypDict(
                    status_code=400,
                    msg="Error : Recovering User",
                    description="A Unknown Error, Please Try Again Later!",
                    success=False
                ) if not isinstance(res,ErrorResponseTypDict) else res
            
            raise HTTPException(
                status_code=detail.status_code,
                detail=detail.model_dump(mode='json')
            )
        
        return SuccessResponseTypDict(
            detail=BaseResponseTypDict(
                status_code=200,
                success=True,
                msg="User recovered successfully"
            )
        )
    
    @catch_errors
    async def get(self):   
        return await UserService(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).get()
    
    @catch_errors
    async def get_by_id(self,userid_toget:str):  
        return await UserService(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).get_by_id(userid_toget=userid_toget)
    
    @catch_errors
    async def get_by_role(self,userrole_toget:UserRoles):    
        return await UserService(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).get_by_role(userrole_toget=userrole_toget)
    

    

    async def search():
        """this is just for abstract this method doesnot do anything"""
        pass