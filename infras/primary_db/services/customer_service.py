from . import BaseServiceModel
from ..models.customer import Customers
from ..repos.customer_repo import CustomersRepo
from ..repos.user_repo import UserRepo
from core.utils.uuid_generator import generate_uuid
from ..models.order import Orders
from sqlalchemy import select,delete,update,or_,func,String
from sqlalchemy.ext.asyncio import AsyncSession
from icecream import ic
from core.data_formats.enums.user_enums import UserRoles
from pydantic import EmailStr
from typing import Optional,List
from schemas.db_schemas.customer import AddCustomerDbSchema,UpdateCustomerDbSchema
from schemas.request_schemas.customer import AddCustomerSchema,UpdateCustomerSchema,AddSearchFields,UpdateSearchFields
from core.decorators.error_handler_dec import catch_errors
from math import ceil
from models.response_models.req_res_models import SuccessResponseTypDict,BaseResponseTypDict,ErrorResponseTypDict
from ..models.ui_id import TablesUiLId
from core.utils.ui_id_generator import generate_ui_id
from core.constants import UI_ID_STARTING_DIGIT,LUI_ID_CUSTOMER_PREFIX
from ...search_engine.models.customer import CustomerSearch
from core.utils.msblob import generate_sas_url,upload_excel_to_blob
from services.sse import sse_manager,sse_msg_builder
from core.utils.percentage_convertor import normalize_percent
from core.utils.safe_date_convertor import safe_date
from core.utils.skipped_data_convertor import write_skipped_items_to_excel
from services.email_service import send_email



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
        cur_uiid=generate_ui_id(prefix=LUI_ID_CUSTOMER_PREFIX,last_id=lui_id)
        data_toadd=data.model_dump(mode='json')
        data_toadd['email']=','.join(data_toadd['emails'])
        del data_toadd['emails']
        ic(data_toadd)
        search_add=AddSearchFields(
            ui_id=cur_uiid,
            id=customer_id,
            name=data.name,
            mobile_number=data.mobile_number,
            email=data_toadd['email'],
            tenant_id=data.tenant_id,
            secondary_domain=data.secondary_domain,
            sector=data.sector,
            industry=data.industry
        )
        # search=await CustomerSearch().create_document(data=search_add.model_dump(mode='json'))
        return await customer_obj.add(data=AddCustomerDbSchema(**data_toadd,id=customer_id,ui_id=cur_uiid,lui_id=lui_id))
    
    async def add_bulk(self,datas:List[dict]):
        skipped_items=[]
        datas_toadd=[]
        duplicate_items=[]

        customer_obj=CustomersRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id)
        lui_id:str=(await self.session.execute(select(TablesUiLId.customer_luiid))).scalar_one_or_none()
        searched_datas=[]
        for data in datas:
            formated_address={}
            # if (await customer_obj.is_customer_exists(email=data['email'],mobile_number=data['mobile_number'])):
            #     skipped_items.append(data)
            #     continue

            customer_id:str=generate_uuid()
            cur_uiid=generate_ui_id(prefix=LUI_ID_CUSTOMER_PREFIX,last_id=lui_id)
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
            search_add=AddSearchFields(
                ui_id=cur_uiid,
                id=customer_id,
                name=data['name'],
                mobile_number=data['mobile_number'],
                email=data['email'],
                tenant_id=data['tenant_id'],
                secondary_domain=data['secondary_domain'],
                sector=data['sector'],
                industry=data['industry']
            ).model_dump(mode='json')
            searched_datas.append(search_add)
            datas_toadd.append(Customers(**data, id=customer_id,ui_id=cur_uiid))
            formated_address={}  
        ic(skipped_items,datas_toadd,duplicate_items)
        # await CustomerSearch().create_bulk_doc(datas=searched_datas)
        return await customer_obj.add_bulk(datas=datas_toadd,lui_id=lui_id)
        
    async def update(self,data:UpdateCustomerSchema):
        data_toupdate=data.model_dump(mode='json',exclude_none=True,exclude_unset=True)
        if 'emails' in data_toupdate:
            data_toupdate['email']=','.join(data_toupdate['emails'])
            del data_toupdate['emails']
            
        if not data_toupdate or len(data_toupdate)<1:
            return ErrorResponseTypDict(status_code=400,success=False,msg="Error : Updating Customer",description="No valid fields to update provided")

        search_data=UpdateSearchFields(
            name=data.name,
            mobile_number=data.mobile_number,
            email=data_toupdate['email'] if 'email' in data_toupdate else None ,
            tenant_id=data.tenant_id,
            secondary_domain=data.secondary_domain,
            sector=data.sector,
            industry=data.industry
        ).model_dump(mode='json',exclude_none=True,exclude_unset=True)

        # await CustomerSearch().update_document(data=search_data,id=data.customer_id)
        return await CustomersRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).update(data=UpdateCustomerDbSchema(**data_toupdate))
        
    @catch_errors
    async def delete(self,customer_id:str,soft_delete:bool=True):
        # await CustomerSearch().delete_document(id=customer_id)
        return await CustomersRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).delete(customer_id=customer_id,soft_delete=soft_delete)
    
    @catch_errors
    async def recover(self,customer_id:str):
        customer=await self.get_by_id(customer_id=customer_id,include_delete=True)
        ic(customer)
        customer_info=customer['customer']
        search_data=AddSearchFields(
            ui_id=customer_info['ui_id'],
            id=customer_info['id'],
            name=customer_info['name'],
            mobile_number=customer_info['mobile_number'],
            email=', '.join(customer_info['emails']),
            tenant_id=customer_info['tenant_id'],
            secondary_domain=customer_info['secondary_domain'],
            sector=customer_info['sector'],
            industry=customer_info['industry']
        ).model_dump(mode='json')
        
        # await CustomerSearch().create_document(data=search_data)
        return await CustomersRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).recover(customer_id=customer_id)

    @catch_errors
    async def get(self,active:bool=False,cursor:int=1,limit:int=10,query:str='',include_deleted:Optional[bool]=False):
        return await CustomersRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).get(active=active,cursor=cursor,limit=limit,query=query,include_deleted=include_deleted)
        
    @catch_errors
    async def search(self,query:str):
        return await CustomersRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).search(query=query)

    @catch_errors
    async def get_by_id(self,customer_id:str,include_delete=False):
        return await CustomersRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).get_by_id(customer_id=customer_id,include_delete=include_delete)



