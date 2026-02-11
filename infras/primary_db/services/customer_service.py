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
from models.response_models.req_res_models import SuccessResponseTypDict,BaseResponseTypDict,ErrorResponseTypDict
from ..models.ui_id import TablesUiLId
from core.utils.ui_id_generator import generate_ui_id
from core.constants import UI_ID_STARTING_DIGIT



class CustomersService(BaseServiceModel):
    def __init__(self,session:AsyncSession,user_role:UserRoles,cur_user_id:str):
        self.session=session
        self.user_role=user_role
        self.cur_user_id=cur_user_id

       
    @catch_errors
    async def add(self,data:AddCustomerSchema):
        # Need to check if the given email or mobile number already exists or not on the customer db
        customer_obj=CustomersRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id)
        # if (await customer_obj.is_customer_exists(email=data.email,mobile_number=data.mobile_number)):
        #     return ErrorResponseTypDict(status_code=400,success=False,msg="Error : Adding Customer",description="Customer with the given email or mobile number already exists")
        
        customer_id:str=generate_uuid()
        lui_id:str=(await self.session.execute(select(TablesUiLId.customer_luiid))).scalar_one_or_none()
        cur_uiid=generate_ui_id(prefix="CUST",last_id=lui_id)
        data_toadd=data.model_dump(mode='json')
        data_toadd['email']=','.join(data_toadd['emails'])
        del data_toadd['emails']
        ic(data_toadd)
        return await customer_obj.add(data=AddCustomerDbSchema(**data_toadd,id=customer_id,ui_id=cur_uiid,lui_id=lui_id))
    
    @catch_errors
    async def add_bulk(self,datas:List[dict]):
        skipped_items=[]
        datas_toadd=[]
        duplicate_items=[]

        customer_obj=CustomersRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id)
        lui_id:str=(await self.session.execute(select(TablesUiLId.customer_luiid))).scalar_one_or_none()
        for data in datas:
            formated_address={}
            # if (await customer_obj.is_customer_exists(email=data['email'],mobile_number=data['mobile_number'])):
            #     skipped_items.append(data)
            #     continue

            customer_id:str=generate_uuid()
            cur_uiid=generate_ui_id(prefix="CUST",last_id=lui_id)
            ic("Before increment : ",lui_id)
            lui_id=cur_uiid
            ic("After increment : ",lui_id)
            formated_address['address']=data['address']
            del data['address']
            formated_address['city']=data['city']
            del data['city']
            formated_address['state']=data['state']
            del data['state']
            formated_address['pincode']=data['pincode']
            del data['pincode']

            data['address']=formated_address
            # if emails.get(data['email']) or mob_nos.get(data['mobile_number']):
            #     duplicate_items.append(data)
            #     continue
            
            # emails[data['email']]=data['email']
            # mob_nos[data['mobile_number']]=data['mobile_number']

            ic(data)
            datas_toadd.append(Customers(**data, id=customer_id,ui_id=cur_uiid))
            formated_address={}      
        ic(skipped_items,datas_toadd,duplicate_items)
        return await customer_obj.add_bulk(datas=datas_toadd,lui_id=lui_id)
        
    @catch_errors  
    async def update(self,data:UpdateCustomerSchema):
        data_toupdate=data.model_dump(mode='json',exclude_none=True,exclude_unset=True)
        data_toupdate['email']=','.join(data_toupdate['emails'])
        del data_toupdate['emails']
        if not data_toupdate or len(data_toupdate)<1:
            return ErrorResponseTypDict(status_code=400,success=False,msg="Error : Updating Customer",description="No valid fields to update provided")
        
        return await CustomersRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).update(data=UpdateCustomerDbSchema(**data_toupdate))
        
    @catch_errors
    async def delete(self,customer_id:str,soft_delete:bool=True):
        return await CustomersRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).delete(customer_id=customer_id,soft_delete=soft_delete)
    
    @catch_errors  
    async def recover(self,customer_id:str):
        return await CustomersRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).recover(customer_id=customer_id)

    @catch_errors
    async def get(self,cursor:int=1,limit:int=10,query:str='',include_deleted:Optional[bool]=False):
        return await CustomersRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).get(cursor=cursor,limit=limit,query=query,include_deleted=include_deleted)
        
    @catch_errors
    async def search(self,query:str):
        return await CustomersRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).search(query=query)

    @catch_errors
    async def get_by_id(self,customer_id:str):
        return await CustomersRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).get_by_id(customer_id=customer_id)



