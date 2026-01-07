from infras.primary_db.services.customer_service import CustomersService
from core.utils.uuid_generator import generate_uuid
from infras.primary_db.models.order import Orders
from sqlalchemy import select,delete,update,or_,func,String
from sqlalchemy.ext.asyncio import AsyncSession
from icecream import ic
from core.data_formats.enums.common_enums import UserRoles
from pydantic import EmailStr
from typing import Optional,List
from schemas.db_schemas.customer import AddCustomerDbSchema,UpdateCustomerDbSchema
from schemas.request_schemas.customer import AddCustomerSchema,UpdateCustomerSchema
from core.decorators.error_handler_dec import catch_errors
from math import ceil
from . import HTTPException,ErrorResponseTypDict,SuccessResponseTypDict,BaseResponseTypDict



class HandleCustomersRequest:
    def __init__(self,session:AsyncSession,user_role:UserRoles):
        self.session=session
        self.user_role=user_role

        if self.user_role==UserRoles.USER.value:
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
    async def add(self,data:AddCustomerSchema):
        res = await CustomersService(session=self.session,user_role=self.user_role).add(data=data)
        if res:
            return SuccessResponseTypDict(
            detail=BaseResponseTypDict(
                status_code=200,
                success=True,
                msg="Customer created successfully"
            )
        )
        
    @catch_errors  
    async def update(self,data:UpdateCustomerSchema):
        res=await CustomersService(session=self.session,user_role=self.user_role).update(data=data)
        if not res:
            raise HTTPException(
                status_code=400,
                detail=ErrorResponseTypDict(
                    status_code=400,
                    success=False,
                    msg="Error : Updaing customer",
                    description="Invalid user input"
                )
            )
        
        return SuccessResponseTypDict(
            detail=BaseResponseTypDict(
                status_code=200,
                success=True,
                msg="Customer updated successfully"
            )
        )
        
    @catch_errors
    async def delete(self,customer_id:str):
        res=await CustomersService(session=self.session,user_role=self.user_role).delete(customer_id=customer_id)
        if not res:
            raise HTTPException(
                status_code=400,
                detail=ErrorResponseTypDict(
                    status_code=400,
                    success=False,
                    msg="Error : Deleting customer",
                    description="Invalid user input"
                )
            )
        
        return SuccessResponseTypDict(
            detail=BaseResponseTypDict(
                status_code=200,
                success=True,
                msg="Customer deleted successfully"
            )
        )
        
    @catch_errors
    async def get(self,offset:int=1,limit:int=10,query:str=''):
        return await CustomersService(session=self.session,user_role=self.user_role).get(offset=offset,limit=limit,query=query)
        
    @catch_errors
    async def search(self,query:str):
        return await CustomersService(session=self.session,user_role=self.user_role).search(query=query)

    @catch_errors
    async def get_by_id(self,customer_id:str):
        return await CustomersService(session=self.session,user_role=self.user_role).get_by_id(customer_id=customer_id)



