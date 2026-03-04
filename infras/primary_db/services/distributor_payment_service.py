from ..models.distributor import DistributorsPayments
from ..models.product import Products
from ..repos.distributor_payment_repo import DistributorsPaymentsRepo
from ..repos.order_repo import OrdersRepo
from core.utils.uuid_generator import generate_uuid
from sqlalchemy import select,delete,update,or_,func,String
from sqlalchemy.ext.asyncio import AsyncSession
from icecream import ic
from pydantic import EmailStr
from typing import Optional,List
from core.data_formats.enums.user_enums import UserRoles
from schemas.request_schemas.distributor_payment import AddDistributorPaymentSchema,UpdateDistributorPaymentSchema
from schemas.db_schemas.distributor_payment import AddDbDistributorPaymentSchema,UpdateDbDistributorPaymentSchema
from core.decorators.db_session_handler_dec import start_db_transaction
from math import ceil
from models.response_models.req_res_models import SuccessResponseTypDict,BaseResponseTypDict,ErrorResponseTypDict
from ..models.user import Users
from ..models.ui_id import TablesUiLId
from . import BaseServiceModel


class DistributorsPaymentsService(BaseServiceModel):
    def __init__(self,session:AsyncSession,user_role:UserRoles,cur_user_id:str):
        self.session=session
        self.user_role=user_role
        self.cur_user_id=cur_user_id

        
    async def add(self,data:AddDistributorPaymentSchema):
        is_order_exists=await OrdersRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).get_by_id(order_id=data.order_id)
        if not is_order_exists or len(is_order_exists['order'])<1:
            return ErrorResponseTypDict(msg="Error : Adding Distributor Payments",status_code=400,success=False,description="Order id doesn't exists")
        
        return await DistributorsPaymentsRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).add(data=AddDbDistributorPaymentSchema(**data.model_dump(mode='json')))
         
    async def update(self,data:UpdateDistributorPaymentSchema):
        is_order_exists=await OrdersRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).get_by_id(order_id=data.order_id)
        if not is_order_exists or len(is_order_exists['order'])<1:
            return ErrorResponseTypDict(msg="Error : Adding Distributor Payments",status_code=400,success=False,description="Order id doesn't exists")
        
        return await DistributorsPaymentsRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).update(data=UpdateDbDistributorPaymentSchema(**data.model_dump(mode='json',exclude=['order_id'])))
    

    async def delete(self,distri_payment_id:str,soft_delete:bool=True):
        return await DistributorsPaymentsRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).delete(distri_payment_id=distri_payment_id,soft_delete=soft_delete)
        
    async def recover(self,distri_payment_id:str):
        return await DistributorsPaymentsRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).recover(distri_payment_id=distri_payment_id)
    
    async def get(self,cursor:int=1,limit:int=10,query:str='',include_deleted:bool=False):
        return await DistributorsPaymentsRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).get(cursor=cursor,limit=limit,query=query,include_deleted=include_deleted)
        
    
    async def search(self,query:str):
        return await DistributorsPaymentsRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).search(query=query)

       
    async def get_by_id(self,distributor_payment_id:str):
        return await DistributorsPaymentsRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).get_by_id(distributor_payment_id=distributor_payment_id)


