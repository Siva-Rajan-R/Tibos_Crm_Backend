from infras.primary_db.services.contact_service import ContactsService
from core.utils.uuid_generator import generate_uuid
from sqlalchemy import select,delete,update,or_,func,String
from sqlalchemy.ext.asyncio import AsyncSession
from icecream import ic
from core.data_formats.enums.common_enums import UserRoles
from pydantic import EmailStr
from typing import Optional,List
from core.decorators.error_handler_dec import catch_errors
from schemas.db_schemas.contact import AddContactDbSchema,UpdateContactDbSchema
from schemas.request_schemas.contact import AddContactSchema,UpdateContactSchema,RecoverContactSchema
from . import HTTPException,ErrorResponseTypDict,SuccessResponseTypDict,BaseResponseTypDict
from core.utils.mob_no_validator import mobile_number_validator



class HandleContactsRequest:
    """on this calss have a multiple methods"""
    def __init__(self,session:AsyncSession,user_role:UserRoles,cur_user_id:str):
        self.session=session
        self.user_role=user_role
        self.cur_user_id=cur_user_id

        # if isinstance(self.user_role,UserRoles):
        #     self.user_role=self.user_role.value

        # if self.user_role==UserRoles.USER.value:
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
    async def add(self,data:AddContactSchema):
        if not mobile_number_validator(mob_no=data.mobile_number):
            raise HTTPException(
                status_code=400,
                detail=ErrorResponseTypDict(
                    status_code=400,
                    success=False,
                    msg="Error : Creating contact ",
                    description="Invalid input data, May be its a mobile number"
                ).model_dump(mode='json')
            )
        
        res = await ContactsService(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).add(data=data)
        if not res or isinstance(res,ErrorResponseTypDict):
            detail:ErrorResponseTypDict=ErrorResponseTypDict(
                    status_code=400,
                    msg="Error : Creating Contact",
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
                msg="Contact created successfully"
            )
        )
        
    @catch_errors  
    async def update(self,data:UpdateContactSchema):
        if data.mobile_number and not mobile_number_validator(mob_no=data.mobile_number):
            raise HTTPException(
                status_code=400,
                detail=ErrorResponseTypDict(
                    status_code=400,
                    success=False,
                    msg="Error : Creating contact ",
                    description="Invalid input data, May be its a mobile number",
                ).model_dump(mode='json')
            )
        res=await ContactsService(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).update(data=data)
        if not res or isinstance(res,ErrorResponseTypDict):
            detail:ErrorResponseTypDict=ErrorResponseTypDict(
                    status_code=400,
                    msg="Error : Updating Contact",
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
                msg="Contact updated successfully"
            )
        )
        
    @catch_errors
    async def delete(self,customer_id:str,contact_id:str,soft_delete:bool=True):
        res=await ContactsService(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).delete(customer_id=customer_id,contact_id=contact_id,soft_delete=soft_delete)
        if not res or isinstance(res,ErrorResponseTypDict):
            detail:ErrorResponseTypDict=ErrorResponseTypDict(
                    status_code=400,
                    msg="Error : Deleting Contact",
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
                msg="Contact deleted successfully"
            )
        )
    
    @catch_errors  
    async def recover(self,data:RecoverContactSchema):
        res=await ContactsService(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).recover(customer_id=data.customer_id,contact_id=data.contact_id)
        if not res or isinstance(res,ErrorResponseTypDict):
            detail:ErrorResponseTypDict=ErrorResponseTypDict(
                    status_code=400,
                    msg="Error : Recovering Contact",
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
                msg="Contact recovered successfully"
            )
        )
    
    @catch_errors  
    async def get(self,cursor:int,limit:int,query:str=''):
        if cursor is None:
            raise HTTPException(
                status_code=400,
                detail=ErrorResponseTypDict(
                    status_code=400,
                    description="No more datas found for contacts",
                    msg="Error : fetching contacts",
                    success=False
                )
            )
        return await ContactsService(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).get(cursor=cursor,limit=limit,query=query)

    @catch_errors
    async def search(self,query:str):
        return await ContactsService(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).search(query=query)

    @catch_errors  
    async def get_by_id(self,contact_id:str):
        return await ContactsService(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).get_by_id(contact_id=contact_id)
    
    @catch_errors
    async def get_by_customer_id(self,customer_id:str,offset:int,limit:int,query:str=''):
        return await ContactsService(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).get_by_customer_id(customer_id=customer_id,offset=offset,limit=limit,query=query)



