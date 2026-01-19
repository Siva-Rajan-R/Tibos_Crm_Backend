from . import BaseServiceModel
from ..models.order import Orders
from ..models.product import Products
from ..models.customer import Customers
from ..repos.product_repo import ProductsRepo
from ..repos.customer_repo import CustomersRepo
from ..repos.distri_repo import DistributorsRepo
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
        # need to check if the customer and the product is exists on the order
        # then check customer is exists or not
        # then chck product is exists or not
        order_obj=OrdersRepo(session=self.session,user_role=self.user_role)
        if (await order_obj.is_order_exists(customer_id=data.customer_id,product_id=data.product_id)):
            return False
        
        cust_exists=await CustomersRepo(session=self.session,user_role=self.user_role).get_by_id(customer_id=data.customer_id)
        if not cust_exists or len(cust_exists)<1:
            return False
        
        prod_exists=await ProductsRepo(session=self.session,user_role=self.user_role).get_by_id(product_id=data.product_id)
        if not prod_exists or len(prod_exists)<1:
            return False
        
        distri_exists=await DistributorsRepo(session=self.session,user_role=self.user_role).get_by_id(distributor_id=data.distributor_id)
        if not distri_exists or len(distri_exists)<1:
            return False
        
        order_id:str=generate_uuid()
        return await order_obj.add(data=AddOrderDbSchema(**data.model_dump(mode='json'),id=order_id))
        # need to implement invoice generation process + email sending
    
    @catch_errors
    async def update(self,data:UpdateOrderSchema):
        data_toupdate=data.model_dump(mode='json',exclude_none=True,exclude_unset=True)
        if not data_toupdate or len(data_toupdate)<1:
            return False
        
        return await OrdersRepo(session=self.session,user_role=self.user_role).update(data=UpdateOrderDbSchema(**data_toupdate))
        
        # need to implement invoice generation process + email sending

    @catch_errors    
    async def delete(self,order_id:str,customer_id:str,soft_delete:bool=True):
        return await OrdersRepo(session=self.session,user_role=self.user_role).delete(order_id=order_id,customer_id=customer_id,soft_delete=soft_delete)
    
    @catch_errors  
    async def recover(self,order_id:str,customer_id:str):
        return await OrdersRepo(session=self.session,user_role=self.user_role).recover(order_id=order_id,customer_id=customer_id)

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



