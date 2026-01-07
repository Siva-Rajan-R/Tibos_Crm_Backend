from . import BaseServiceModel
from ..models.order import Orders
from ..models.product import Products
from ..models.customer import Customers
from core.utils.uuid_generator import generate_uuid
from ..repos.order_repo import OrdersRepo
from sqlalchemy import select,delete,update,or_,func,String
from sqlalchemy.ext.asyncio import AsyncSession
from icecream import ic
from core.data_formats.enums.common_enums import UserRoles
from core.data_formats.enums.pg_enums import PaymentStatus,InvoiceStatus
from core.data_formats.typed_dicts.pg_dict import DeliveryInfo
from schemas.db_schemas.order import AddOrderDbSchema,UpdateOrderDbSchema
from schemas.request_schemas.order import AddOrderSchema,UpdateOrderSchema
from core.decorators.error_handler_dec import catch_errors
from math import ceil



class OrdersService(BaseServiceModel):
    def __init__(self,session:AsyncSession,user_role:UserRoles):
        self.session=session
        self.user_role=user_role


    @catch_errors
    async def add(self,data:AddOrderSchema):
        order_id:str=generate_uuid()
        return await OrdersRepo(session=self.session,user_role=self.user_role).add(data=AddOrderDbSchema(**data.model_dump(mode='json'),id=order_id))
        # need to implement invoice generation process + email sending
    
    @catch_errors
    async def update(self,data:UpdateOrderSchema):
        data_toupdate=data.model_dump(mode='json',exclude_none=True,exclude_unset=True)
        if not data_toupdate or len(data_toupdate)<1:
            return False
        
        return await OrdersRepo(session=self.session,user_role=self.user_role).update(data=UpdateOrderDbSchema(**data_toupdate))
        
        # need to implement invoice generation process + email sending

    @catch_errors    
    async def delete(self,order_id:str,customer_id:str):
        return await OrdersRepo(session=self.session,user_role=self.user_role).delete(order_id=order_id,customer_id=customer_id)

    @catch_errors
    async def get(self,offset:int=1,limit:int=10,query:str=''):
        return await OrdersRepo(session=self.session,user_role=self.user_role).get(offset=offset,limit=limit,query=query)
    
    @catch_errors
    async def search(self,query:str):
        return await OrdersRepo(session=self.session,user_role=self.user_role).search(query=query)

    @catch_errors  
    async def get_by_id(self,order_id:str):
        return await OrdersRepo(session=self.session,user_role=self.user_role).get_by_id(order_id=order_id)
        
    @catch_errors
    async def get_by_customer_id(self,customer_id:str,offset:int,limit:int):
        return await OrdersRepo(session=self.session,user_role=self.user_role).get_by_customer_id(customer_id=customer_id,offset=offset,limit=limit)



