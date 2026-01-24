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
    def __init__(self,session:AsyncSession,user_role:UserRoles,cur_user_id:str):
        self.session=session
        self.user_role=user_role
        self.cur_user_id=cur_user_id

       
    @catch_errors
    async def add(self,data:AddCustomerSchema):
        # Need to check if the given email or mobile number already exists or not on the customer db
        customer_obj=CustomersRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id)
        if (await customer_obj.is_customer_exists(email=data.email,mobile_number=data.mobile_number)):
            return False
        
        customer_id:str=generate_uuid()
        return await customer_obj.add(data=AddCustomerDbSchema(**data.model_dump(mode='json'),id=customer_id))
        
    @catch_errors  
    async def update(self,data:UpdateCustomerSchema):
        data_toupdate=data.model_dump(mode='json',exclude_none=True,exclude_unset=True)

        if not data_toupdate or len(data_toupdate)<1:
            return False
        
        return await CustomersRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).update(data=UpdateCustomerDbSchema(**data_toupdate))
        
    @catch_errors
    async def delete(self,customer_id:str,soft_delete:bool=True):
        return await CustomersRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).delete(customer_id=customer_id,soft_delete=soft_delete)
    
    @catch_errors  
    async def recover(self,customer_id:str):
        return await CustomersRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).recover(customer_id=customer_id)

    @catch_errors
    async def get(self,offset:int=1,limit:int=10,query:str='',include_deleted:Optional[bool]=False):
        return await CustomersRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).get(offset=offset,limit=limit,query=query,include_deleted=include_deleted)
        
    @catch_errors
    async def search(self,query:str):
        return await CustomersRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).search(query=query)

    @catch_errors
    async def get_by_id(self,customer_id:str):
        return await CustomersRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).get_by_id(customer_id=customer_id)



