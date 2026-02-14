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
from core.data_formats.enums.common_enums import UserRoles
from pydantic import EmailStr
from typing import Optional,List
from schemas.db_schemas.distributor import CreateDistriDbSchema,UpdateDistriDbSchema
from schemas.request_schemas.distributor import CreateDistriSchema,UpdateDistriSchema
from core.decorators.error_handler_dec import catch_errors
from math import ceil
from models.response_models.req_res_models import SuccessResponseTypDict,BaseResponseTypDict,ErrorResponseTypDict
from ..models.ui_id import TablesUiLId
from core.utils.ui_id_generator import generate_ui_id
from core.constants import UI_ID_STARTING_DIGIT
from schemas.request_schemas.order import OrderFilterSchema


class DistributorService(BaseServiceModel):
    def __init__(self,session:AsyncSession,user_role:UserRoles,cur_user_id:str):
        self.session=session
        self.user_role=user_role
        self.cur_user_id=cur_user_id

       
    @catch_errors
    async def add(self,data:CreateDistriSchema):
        
        distri_id:str=generate_uuid()
        lui_id:str=(await self.session.execute(select(TablesUiLId.distri_luiid))).scalar_one_or_none()
        cur_uiid=generate_ui_id(prefix="DIST",last_id=lui_id)
        return await DistributorsRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).add(data=CreateDistriDbSchema(**data.model_dump(mode='json'),id=distri_id,ui_id=cur_uiid,lui_id=lui_id))

    @catch_errors
    async def add_bulk(self,datas:List[dict]):
        skipped_items=[]
        
        datas_toadd=[]
        distri_obj=DistributorsRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id)
        lui_id:str=(await self.session.execute(select(TablesUiLId.distri_luiid))).scalar_one_or_none()
        for data in datas:
            distri_id:str=generate_uuid()
            cur_uiid=generate_ui_id(prefix="DIST",last_id=lui_id)
            ic("Before increment : ",lui_id)
            lui_id=cur_uiid
            ic("After increment : ",lui_id)
            data['discount']=str(data['discount']*100)+"%"
            datas_toadd.append(Distributors(**data, id=distri_id,ui_id=cur_uiid))
                
        ic(skipped_items,datas_toadd)
        return await distri_obj.add_bulk(datas=datas_toadd,lui_id=lui_id)
        
    @catch_errors  
    async def update(self,data:UpdateDistriSchema):
        data_toupdate=data.model_dump(mode='json',exclude_none=True,exclude_unset=True)

        if not data_toupdate or len(data_toupdate)<1:
            return ErrorResponseTypDict(status_code=400,success=False,msg="Error : Updating Distributor",description="No valid fields to update provided")
        
        return await DistributorsRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).update(data=UpdateDistriDbSchema(**data_toupdate))
        
    @catch_errors
    async def delete(self,distributor_id:str,soft_delete:bool=True):
        have_order=(await OrdersRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).get(query=distributor_id,limit=1,filter=OrderFilterSchema())).get('orders')
        if have_order or len(have_order)>0:
            return ErrorResponseTypDict(status_code=400,success=False,msg="Error : Deleting Distributor",description="Distributor has associated orders and cannot be deleted")
        
        return await DistributorsRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).delete(distri_id=distributor_id,soft_delete=soft_delete)
    
    @catch_errors
    async def recover(self,distributor_id:str):
        return await DistributorsRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).recover(distri_id=distributor_id)
     
    @catch_errors
    async def get(self,cursor:int=1,limit:int=10,query:str='',include_deleted:Optional[bool]=False):
        return await DistributorsRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).get(cursor=cursor,limit=limit,query=query,include_deleted=include_deleted)
        
    @catch_errors
    async def search(self,query:str):
        return await DistributorsRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).search(query=query)

    @catch_errors
    async def get_by_id(self,distributor_id:str):
        return await DistributorsRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).get_by_id(distributor_id=distributor_id)



