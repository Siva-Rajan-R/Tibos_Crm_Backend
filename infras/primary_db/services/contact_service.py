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
from models.response_models.req_res_models import SuccessResponseTypDict,BaseResponseTypDict,ErrorResponseTypDict
from ..models.ui_id import TablesUiLId
from core.utils.ui_id_generator import generate_ui_id
from core.constants import UI_ID_STARTING_DIGIT



class ContactsService(BaseServiceModel):
    """on this calss have a multiple methods"""
    def __init__(self,session:AsyncSession,user_role:UserRoles,cur_user_id:str):
        self.session=session
        self.user_role=user_role
        self.cur_user_id=cur_user_id


        

    @catch_errors
    async def add(self,data:AddContactSchema):
        """using this method we can add the contacts to the db"""
        # check the give customer id is already exists on the Customers db
        # then check the email or number that matches to the customer_id that matches to the contact db

        
        contact_obj=ContactsRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id)
        if (await contact_obj.is_contact_exists(email=data.email,mobile_number=data.mobile_number,customer_id=data.customer_id)):
            return ErrorResponseTypDict(status_code=400,success=False,msg="Error : Adding Contact",description="Contact with the given email or mobile number already exists for the customer")
        
        is_cust_exists=await CustomersRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).get_by_id(customer_id=data.customer_id)
        if not is_cust_exists['customer'] or len(is_cust_exists['customer'])<1:
            return ErrorResponseTypDict(status_code=400,success=False,msg="Error : Adding Contact",description="Customer with the given id does not exist")
        
        contact_id=generate_uuid(data=data.name)
        lui_id:str=(await self.session.execute(select(TablesUiLId.contact_luiid))).scalar_one_or_none()
        cur_uiid=generate_ui_id(prefix="CONTC",last_id=lui_id)

        return await contact_obj.add(data=AddContactDbSchema(**data.model_dump(mode='json'),id=contact_id,ui_id=cur_uiid,lui_id=lui_id))

    @catch_errors
    async def add_bulk(self,datas:List[dict]):
        skipped_items=[]
        datas_toadd=[]
        
        contact_obj=ContactsRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id)
        lui_id:str=(await self.session.execute(select(TablesUiLId.contact_luiid))).scalar_one_or_none()
        for data in datas:
            is_cust_exists=await CustomersRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).get_by_id(customer_id=data['customer_id'])
            if not is_cust_exists['customer'] or len(is_cust_exists['customer'])<1:
                skipped_items.append(data)
                continue

            data['customer_id']=is_cust_exists['customer']['id']

            if (await contact_obj.is_contact_exists(email=data['email'],mobile_number=data['mobile_number'],customer_id=data['customer_id'])):
                skipped_items.append(data)
                continue
            
            contact_id:str=generate_uuid()
            
            cur_uiid=generate_ui_id(prefix="CONTC",last_id=lui_id)
            ic("Before increment : ",lui_id)
            lui_id=cur_uiid
            ic("After increment : ",lui_id)
            datas_toadd.append(Contacts(**data, id=contact_id,ui_id=cur_uiid))
        ic(skipped_items,datas_toadd)
        return await contact_obj.add_bulk(datas=datas_toadd,lui_id=lui_id)
       
    @catch_errors  
    async def update(self,data:UpdateContactSchema):
        data_toupdate=data.model_dump(mode='json',exclude_unset=True,exclude_none=True)
        if not data_toupdate or len(data_toupdate)<1:
            return ErrorResponseTypDict(status_code=400,success=False,msg="Error : Updating Contact",description="No valid fields to update provided")
        
        return await ContactsRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).update(data=UpdateContactDbSchema(**data_toupdate))
        
    @catch_errors
    async def delete(self,customer_id:str,contact_id:str,soft_delete:bool=True):
        return await ContactsRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).delete(customer_id=customer_id,contact_id=contact_id,soft_delete=soft_delete)
    
    @catch_errors  
    async def recover(self,customer_id:str,contact_id:str):
        return await ContactsRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).recover(customer_id=customer_id,contact_id=contact_id)

    @catch_errors  
    async def get(self,cursor:int,limit:int,query:str='',include_deleted:Optional[bool]=False):
        return await ContactsRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).get(cursor=cursor,limit=limit,query=query,include_deleted=include_deleted)

    @catch_errors
    async def search(self,query:str):
        return await ContactsRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).search(query=query)

    @catch_errors  
    async def get_by_id(self,contact_id:str):
        return await ContactsRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).get_by_id(contact_id=contact_id)
    
    @catch_errors
    async def get_by_customer_id(self,customer_id:str,offset:int,limit:int,query:str=''):
        return await ContactsRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).get_by_customer_id(customer_id=customer_id,offset=offset,limit=limit,query=query)



