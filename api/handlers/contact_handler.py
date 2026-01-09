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
from schemas.request_schemas.contact import AddContactSchema,UpdateContactSchema
from . import HTTPException,ErrorResponseTypDict,SuccessResponseTypDict,BaseResponseTypDict
from core.utils.mob_no_validator import mobile_number_validator



class HandleContactsRequest:
    """on this calss have a multiple methods"""
    def __init__(self,session:AsyncSession,user_role:UserRoles):
        self.session=session
        self.user_role=user_role

        if self.user_role.value==UserRoles.USER.value:
            raise HTTPException(
                status_code=401,
                detail=ErrorResponseTypDict(
                    msg="Error : ",
                    description="Insufficient permission",
                    status_code=401,
                    success=False
                )
            )
        

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
                )
            )
        
        res = await ContactsService(session=self.session,user_role=self.user_role).add(data=data)
        if res:
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
                    description="Invalid input data, May be its a mobile number"
                )
            )
        res=await ContactsService(session=self.session,user_role=self.user_role).update(data=data)
        if not res:
            raise HTTPException(
                status_code=400,
                detail=ErrorResponseTypDict(
                    status_code=400,
                    success=False,
                    msg="Error : Updaing contact",
                    description="Invalid user input"
                )
            )
        
        return SuccessResponseTypDict(
            detail=BaseResponseTypDict(
                status_code=200,
                success=True,
                msg="Contact updated successfully"
            )
        )
        
    @catch_errors
    async def delete(self,customer_id:str,contact_id:str):
        res=await ContactsService(session=self.session,user_role=self.user_role).delete(customer_id=customer_id,contact_id=contact_id)
        if not res:
            raise HTTPException(
                status_code=400,
                detail=ErrorResponseTypDict(
                    status_code=400,
                    success=False,
                    msg="Error : Deleting contact",
                    description="Invalid user input"
                )
            )
        
        return SuccessResponseTypDict(
            detail=BaseResponseTypDict(
                status_code=200,
                success=True,
                msg="Contact deleted successfully"
            )
        )
    
    @catch_errors  
    async def get(self,offset:int,limit:int,query:str=''):
        return await ContactsService(session=self.session,user_role=self.user_role).get(offset=offset,limit=limit,query=query)

    @catch_errors
    async def search(self,query:str):
        return await ContactsService(session=self.session,user_role=self.user_role).search(query=query)

    @catch_errors  
    async def get_by_id(self,contact_id:str):
        return await ContactsService(session=self.session,user_role=self.user_role).get_by_id(contact_id=contact_id)
    
    @catch_errors
    async def get_by_customer_id(self,customer_id:str,offset:int,limit:int,query:str=''):
        return await ContactsService(session=self.session,user_role=self.user_role).get_by_customer_id(customer_id=customer_id,offset=offset,limit=limit,query=query)



