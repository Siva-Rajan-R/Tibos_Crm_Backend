from . import BaseServiceModel
from ..models.contact import Contacts
from ..models.order import Orders
from ..models.customer import Customers
from ..repos.customer_repo import CustomersRepo
from core.utils.uuid_generator import generate_uuid
from sqlalchemy import select,delete,update,or_,func,String
from sqlalchemy.ext.asyncio import AsyncSession
from icecream import ic
from core.data_formats.enums.common_enums import UserRoles
from pydantic import EmailStr
from typing import Optional,List
from math import ceil
from core.decorators.error_handler_dec import catch_errors
from schemas.db_schemas.contact import AddContactDbSchema,UpdateContactDbSchema
from schemas.request_schemas.contact import AddContactSchema,UpdateContactSchema
from ..repos.contact_repo import ContactsRepo



class ContactsService(BaseServiceModel):
    """on this calss have a multiple methods"""
    def __init__(self,session:AsyncSession,user_role:UserRoles):
        self.session=session
        self.user_role=user_role

        

    @catch_errors
    async def add(self,data:AddContactSchema):
        """using this method we can add the contacts to the db"""
        # check the give customer id is already exists on the Customers db
        # then check the email or number that matches to the customer_id that matches to the contact db

        
        contact_obj=ContactsRepo(session=self.session,user_role=self.user_role)
        if (await contact_obj.is_contact_exists(email=data.email,mobile_number=data.mobile_number,customer_id=data.customer_id)):
            return False
        
        is_cust_exists=await CustomersRepo(session=self.session).get_by_id(customer_id=data.customer_id)
        if not is_cust_exists or len(is_cust_exists)<1:
            return False
        
        contact_id=generate_uuid(data=data.name)
        return await contact_obj.add(data=AddContactDbSchema(**data.model_dump(mode='json'),id=contact_id))
        
    @catch_errors  
    async def update(self,data:UpdateContactSchema):
        data_toupdate=data.model_dump(mode='json',exclude_unset=True,exclude_none=True)
        if not data_toupdate or len(data_toupdate)<1:
            return False
        
        return await ContactsRepo(session=self.session,user_role=self.user_role).update(data=UpdateContactDbSchema(**data_toupdate))
        
    @catch_errors
    async def delete(self,customer_id:str,contact_id:str):
        return await ContactsRepo(session=self.session,user_role=self.user_role).delete(customer_id=customer_id,contact_id=contact_id)
    
    @catch_errors  
    async def get(self,offset:int,limit:int,query:str=''):
        return await ContactsRepo(session=self.session,user_role=self.user_role).get(offset=offset,limit=limit,query=query)

    @catch_errors
    async def search(self,query:str):
        return await ContactsRepo(session=self.session,user_role=self.user_role).search(query=query)

    @catch_errors  
    async def get_by_id(self,contact_id:str):
        return await ContactsRepo(session=self.session,user_role=self.user_role).get_by_id(contact_id=contact_id)
    
    @catch_errors
    async def get_by_customer_id(self,customer_id:str,offset:int,limit:int,query:str=''):
        return await ContactsRepo(session=self.session,user_role=self.user_role).get_by_customer_id(customer_id=customer_id,offset=offset,limit=limit,query=query)



