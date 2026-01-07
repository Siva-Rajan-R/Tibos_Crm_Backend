from . import BaseServiceModel
from ..models.customer import Customers,CustomerIndustries,CustomerSectors
from ..repos.customer_repo import CustomersRepo
from core.utils.uuid_generator import generate_uuid
from ..models.order import Orders
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



class CustomersService(BaseServiceModel):
    def __init__(self,session:AsyncSession,user_role:UserRoles):
        self.session=session
        self.user_role=user_role

       
    @catch_errors
    async def add(self,data:AddCustomerSchema):
        customer_id:str=generate_uuid()
        return await CustomersRepo(session=self.session,user_role=self.user_role).add(data=AddCustomerDbSchema(**data.model_dump(mode='json'),id=customer_id))
        
    @catch_errors  
    async def update(self,data:UpdateCustomerSchema):
        data_toupdate=data.model_dump(mode='json',exclude_none=True,exclude_unset=True)

        if not data_toupdate or len(data_toupdate)<1:
            return False
        
        return await CustomersRepo(session=self.session,user_role=self.user_role).update(data=UpdateCustomerDbSchema(**data_toupdate))
        
    @catch_errors
    async def delete(self,customer_id:str):
        return await CustomersRepo(session=self.session,user_role=self.user_role).delete(customer_id=customer_id)
        
    @catch_errors
    async def get(self,offset:int=1,limit:int=10,query:str=''):
        return await CustomersRepo(session=self.session,user_role=self.user_role).get(offset=offset,limit=limit,query=query)
        
    @catch_errors
    async def search(self,query:str):
        return await CustomersRepo(session=self.session,user_role=self.user_role).search(query=query)

    @catch_errors
    async def get_by_id(self,customer_id:str):
        return await CustomersRepo(session=self.session,user_role=self.user_role).get_by_id(customer_id=customer_id)



