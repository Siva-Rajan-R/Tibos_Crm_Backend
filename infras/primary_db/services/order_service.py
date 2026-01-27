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
from typing import Optional
from models.response_models.req_res_models import SuccessResponseTypDict,BaseResponseTypDict,ErrorResponseTypDict



class OrdersService(BaseServiceModel):
    def __init__(self,session:AsyncSession,user_role:UserRoles,cur_user_id:str):
        self.session=session
        self.user_role=user_role
        self.cur_user_id=cur_user_id


    @catch_errors
    async def add(self,data:AddOrderSchema):
        # need to check if the customer and the product is exists on the order
        # then check customer is exists or not
        # then chck product is exists or not
        order_obj=OrdersRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id)
        if (await order_obj.is_order_exists(customer_id=data.customer_id,product_id=data.product_id)):
            return ErrorResponseTypDict(status_code=400,success=False,msg="Error : Adding Order",description="Order with the given customer id and product id already exists")
        
        cust_exists=await CustomersRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).get_by_id(customer_id=data.customer_id)
        if not cust_exists or len(cust_exists)<1:
            return ErrorResponseTypDict(status_code=400,success=False,msg="Error : Adding Order",description="Customer with the given id does not exist")
        
        prod_exists=await ProductsRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).get_by_id(product_id=data.product_id)
        if not prod_exists or len(prod_exists)<1:
            return ErrorResponseTypDict(status_code=400,success=False,msg="Error : Adding Order",description="Product with the given id does not exist")
        
        distri_exists=await DistributorsRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).get_by_id(distributor_id=data.distributor_id)
        if not distri_exists or len(distri_exists)<1:
            return ErrorResponseTypDict
        
        order_id:str=generate_uuid()
        return await order_obj.add(data=AddOrderDbSchema(**data.model_dump(mode='json'),id=order_id))
        # need to implement invoice generation process + email sending
    
    @catch_errors
    async def update(self,data:UpdateOrderSchema):
        data_toupdate=data.model_dump(mode='json',exclude_none=True,exclude_unset=True)
        if not data_toupdate or len(data_toupdate)<1:
            return ErrorResponseTypDict(status_code=400,success=False,msg="Error : Updating Order",description="No valid fields to update provided")
        
        return await OrdersRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).update(data=UpdateOrderDbSchema(**data_toupdate))
        
        # need to implement invoice generation process + email sending

    @catch_errors    
    async def delete(self,order_id:str,customer_id:str,soft_delete:bool=True):
        return await OrdersRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).delete(order_id=order_id,customer_id=customer_id,soft_delete=soft_delete)
    
    @catch_errors  
    async def recover(self,order_id:str,customer_id:str):
        return await OrdersRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).recover(order_id=order_id,customer_id=customer_id)

    @catch_errors
    async def get(self,offset:int=1,limit:int=10,query:str='',include_deleted:Optional[bool]=False):
        return await OrdersRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).get(offset=offset,limit=limit,query=query,include_deleted=include_deleted)
    
    @catch_errors
    async def search(self,query:str):
        return await OrdersRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).search(query=query)

    @catch_errors  
    async def get_by_id(self,order_id:str):
        return await OrdersRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).get_by_id(order_id=order_id)
        
    @catch_errors
    async def get_by_customer_id(self,customer_id:str,offset:int,limit:int):
        return await OrdersRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).get_by_customer_id(customer_id=customer_id,offset=offset,limit=limit)



