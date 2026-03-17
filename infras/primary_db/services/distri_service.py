from . import BaseServiceModel
from ..repos.product_repo import ProductsRepo
from ..models.distributor import Distributors
from ..repos.distri_repo import DistributorsRepo
from ..repos.order_repo import OrdersRepo
from core.utils.uuid_generator import generate_uuid
from ..models.order import Orders
from sqlalchemy import select,delete,update,or_,func,String
from sqlalchemy.ext.asyncio import AsyncSession
from icecream import ic
from core.data_formats.enums.user_enums import UserRoles
from pydantic import EmailStr
from typing import Optional,List
from schemas.db_schemas.distributor import CreateDistriDbSchema,UpdateDistriDbSchema
from schemas.request_schemas.distributor import CreateDistriSchema,UpdateDistriSchema,AddSearchFields,UpdateSearchFields
from core.decorators.error_handler_dec import catch_errors
from math import ceil
from models.response_models.req_res_models import SuccessResponseTypDict,BaseResponseTypDict,ErrorResponseTypDict
from ..models.ui_id import TablesUiLId
from core.utils.ui_id_generator import generate_ui_id
from core.constants import UI_ID_STARTING_DIGIT,LUI_ID_DISTRI_PREFIX
from schemas.request_schemas.order import OrderFilterSchema
from core.data_formats.enums.order_enums import DistributorType
from core.utils.discount_validator import validate_discount
from ...search_engine.models.distributor import DistributorSearch
from ..repos.user_repo import UserRepo
from core.utils.msblob import generate_sas_url,upload_excel_to_blob
from services.sse import sse_manager,sse_msg_builder
from core.utils.percentage_convertor import normalize_percent
from core.utils.safe_date_convertor import safe_date
from core.utils.skipped_data_convertor import write_skipped_items_to_excel
from services.email_service import send_email


class DistributorService(BaseServiceModel):
    def __init__(self,session:AsyncSession,user_role:UserRoles,cur_user_id:str):
        self.session=session
        self.user_role=user_role
        self.cur_user_id=cur_user_id

       
    @catch_errors
    async def add(self,data:CreateDistriSchema):
        filterd_set=set()
        for i in data.discounts:
            discount=validate_discount(i.get('discount'))
            ic(discount)
            if discount is None:
                break
            filterd_set.add(f"{i.get('rebate_type')}-{discount}")
            ic(filterd_set)

        if len(filterd_set)!=len(data.discounts):
            return ErrorResponseTypDict(status_code=400,success=False,msg="Error : Adding Distributor",description="Multiple same discount format was found")
        
        final_discounts={}
        for discount in data.discounts:
            discount_id:str=generate_uuid()
            final_discounts[discount_id]={**discount,'id':discount_id}

        lui_id:str=(await self.session.execute(select(TablesUiLId.distri_luiid))).scalar_one_or_none()
        distri_obj=DistributorsRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id)
        distri_id:str=generate_uuid()
        cur_uiid=generate_ui_id(prefix=LUI_ID_DISTRI_PREFIX,last_id=lui_id)
        data_toadd=data.model_dump(mode='json')
        data_toadd['name']=data_toadd['name'].upper()
        data_toadd['discounts']=final_discounts

        search_fields=AddSearchFields(
            name=data.name,
            id=distri_id,
            ui_id=cur_uiid
        ).model_dump(mode="json")

        # await DistributorSearch().create_document(data=search_fields)
        return await distri_obj.add(data=CreateDistriDbSchema(**data_toadd,id=distri_id,lui_id=lui_id,ui_id=cur_uiid))

    @catch_errors
    async def add_bulk(self,datas:List[dict]):
        skipped_items=[]
        searchable_datas=[]
        datas_toadd=[]
        distri_obj=DistributorsRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id)
        lui_id:str=(await self.session.execute(select(TablesUiLId.distri_luiid))).scalar_one_or_none()
        for data in datas:
            filterd_set=set()
            for i in data['discounts']:
                discount=validate_discount(i.get('discount'))
                ic(discount)
                if discount is None:
                    break
                filterd_set.add(f"{i.get('rebate_type')}-{discount}")
                ic(filterd_set)

            if len(filterd_set)!=len(data['discounts']):
                data['reason']="Some of the discounts are similar"
                skipped_items.append(data)
                continue
            
            final_discounts={}
            for discount in data['discounts']:
                discount_id:str=generate_uuid()
                final_discounts[discount_id]={**discount,'id':discount_id}
            
            distri_id:str=generate_uuid()
            cur_uiid=generate_ui_id(prefix=LUI_ID_DISTRI_PREFIX,last_id=lui_id)
            lui_id=cur_uiid
            data['discounts']=final_discounts
            search_fields=AddSearchFields(
                id=distri_id,
                ui_id=cur_uiid,
                name=data['name']
            ).model_dump(mode="json")
            searchable_datas.append(search_fields)
            datas_toadd.append(Distributors(**data, id=distri_id,ui_id=cur_uiid))
                
        skipped_file_path = write_skipped_items_to_excel(skipped_items)
        
        ic("skipped_items_count", len(skipped_items))
        ic("orders_to_insert_count", len(datas_toadd))
        ic("Skipped file path",skipped_file_path)
        data['is_deleted']=True
        if len(skipped_items)>0:
            blob_name=upload_excel_to_blob(local_file_path=skipped_file_path)
            url=generate_sas_url(blob_name=blob_name)
            ic(url)
            msg=sse_msg_builder(title="Skiped datas report",description=f"During bulk upload these are the datas are skipped, Skipped Items Count ({len(skipped_items)}), Added Items Count ({len(datas_toadd)})",type="file",url=url)
            is_sended=await sse_manager.send(self.cur_user_id,data=msg)
            if not is_sended:
                user=await UserRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).get_by_id(userid_toget=self.cur_user_id)
                user_email=user['user']['email']
                await send_email(client_ip="",reciver_emails=[user_email],subject="Skiped datas report",body=f"Skipped Items Count ({len(skipped_items)}), Added Items Count ({len(datas_toadd)}), During bulk upload these are the datas are skipped -> {url}",is_html=False,sender_email_id="crm@tibos.in")

        # await DistributorSearch().create_bulk_doc(datas=searchable_datas)
        return await distri_obj.add_bulk(datas=datas_toadd,lui_id=lui_id)
        
  
    async def update(self,data:UpdateDistriSchema):
        filterd_set=set()
        for i in data.discounts:
            discount=validate_discount(i.get('discount'))
            if discount is None:
                break
            filterd_set.add(f"{i.get('rebate_type')}-{discount}")
            
        if len(filterd_set)!=len(data.discounts):
            return ErrorResponseTypDict(status_code=400,success=False,msg="Error : Updating Distributor",description="Multiple same discount format was found")
        
        final_discounts={}
        for discount in data.discounts:
            discount_id:str=generate_uuid()
            if 'id' not in discount:
                final_discounts[discount_id]={**discount,'id':discount_id}

        data_toupdate=data.model_dump(mode='json',exclude_none=True,exclude_unset=True)
        distri_obj=DistributorsRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id)
        if not data_toupdate or len(data_toupdate)<1:
            return ErrorResponseTypDict(status_code=400,success=False,msg="Error : Updating Distributor",description="No valid fields to update provided")
        
        data_toupdate['name']=data_toupdate['name'].upper()
        data_toupdate['discounts']=final_discounts

        if not (await distri_obj.get_by_id(distributor_id=data_toupdate['name']))['distributors']:
            return ErrorResponseTypDict(status_code=400,success=False,msg="Error : Updating Distributor",description="Distributor name already exists")
        
        search_fields=UpdateSearchFields(
            name=data.name
        ).model_dump(mode="json")

        # await DistributorSearch().update_document(data=search_fields,id=data.id)
        return await distri_obj.update(data=UpdateDistriDbSchema(**data_toupdate))
        
    @catch_errors
    async def delete(self,distributor_id:str,soft_delete:bool=True):
        have_order=(await OrdersRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).get(query=distributor_id,limit=1,filter=OrderFilterSchema())).get('orders')
        if have_order or len(have_order)>0:
            return ErrorResponseTypDict(status_code=400,success=False,msg="Error : Deleting Distributor",description="Distributor has associated orders and cannot be deleted")
        # await DistributorSearch().delete_document(id=distributor_id)
        return await DistributorsRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).delete(distri_id=distributor_id,soft_delete=soft_delete)
    
    @catch_errors
    async def recover(self,distributor_id:str):
        distri=await self.get_by_id(distributor_id=distributor_id,include_delete=True)
        distri_info=distri['distributors']
        search_fields=AddSearchFields(
            name=distri_info['name'],
            id=distri_info['id'],
            ui_id=distri_info['ui_id']
        ).model_dump(mode="json")

        # await DistributorSearch().create_document(data=search_fields)
        return await DistributorsRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).recover(distri_id=distributor_id)
     
    @catch_errors
    async def get(self,cursor:int=1,limit:int=10,query:str='',include_deleted:Optional[bool]=False):
        return await DistributorsRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).get(cursor=cursor,limit=limit,query=query,include_deleted=include_deleted)
        
    @catch_errors
    async def search(self,query:str):
        return await DistributorsRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).search(query=query)

    @catch_errors
    async def get_by_id(self,distributor_id:str,include_delete:bool=False):
        return await DistributorsRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).get_by_id(distributor_id=distributor_id,include_delete=include_delete)



