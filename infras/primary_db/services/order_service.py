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
from core.data_formats.enums.user_enums import UserRoles
from core.data_formats.enums.order_enums import PurchaseTypes
from core.data_formats.typed_dicts.order_typdict import DeliveryInfo
from schemas.db_schemas.order import AddOrderDbSchema,UpdateOrderDbSchema
from schemas.request_schemas.order import AddOrderSchema,UpdateOrderSchema
from core.decorators.error_handler_dec import catch_errors
from math import ceil
from typing import Optional,List
from models.response_models.req_res_models import SuccessResponseTypDict,BaseResponseTypDict,ErrorResponseTypDict
from ..models.ui_id import TablesUiLId
from core.utils.ui_id_generator import generate_ui_id
from core.constants import UI_ID_STARTING_DIGIT,LUI_ID_ORDER_PREFIX
from core.utils.discount_validator import parse_discount

import pandas as pd
from schemas.request_schemas.order import OrderFilterSchema
from core.utils.calculations import get_distributor_price,get_remaining_days
from core.data_formats.typed_dicts.order_typdict import DeliveryInfo,StatusInfo,LogisticsInfo



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
        
        cust_exists=await CustomersRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).get_by_id(customer_id=data.customer_id)
        if not cust_exists or len(cust_exists)<1:
            return ErrorResponseTypDict(status_code=400,success=False,msg="Error : Adding Order",description="Customer with the given id does not exist")
        
        prod_exists=await ProductsRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).get_by_id(product_id=data.product_id)
        if not prod_exists or len(prod_exists)<1:
            return ErrorResponseTypDict(status_code=400,success=False,msg="Error : Adding Order",description="Product with the given id does not exist")
        
        distri_exists=await DistributorsRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).get_by_id(distributor_id=data.distributor_id)
        if not distri_exists or len(distri_exists)<1:
            return ErrorResponseTypDict(status_code=400,success=False,msg="Error : Adding Order",description="Distributor with the given id does not exist")

        data_toadd=data.model_dump(mode='json')
        if data.logistic_info.get('purchase_type').value==PurchaseTypes.EXISTING_ADD_ON.value:
            last_order=await order_obj.get_last_order(customer_id=cust_exists['customer']['id'],product_id=prod_exists['product']['id'])
            last_ord_expiry_date=last_order.get('last_order')['expiry_date']
            data_toadd['logistic_info']['last_ord_expiry_date']=last_ord_expiry_date

        order_id:str=generate_uuid()

        lui_id:str=(await self.session.execute(select(TablesUiLId.order_luiid))).scalar_one_or_none()
        cur_uiid=generate_ui_id(prefix=LUI_ID_ORDER_PREFIX,last_id=lui_id)
        return await order_obj.add(data=AddOrderDbSchema(**data_toadd,id=order_id,ui_id=cur_uiid))
    
    @catch_errors
    async def add_bulk(self,datas:List[dict]):
        skipped_items=[]
        datas_toadd=[]

        orders_obj=OrdersRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id)
        lui_id:str=(await self.session.execute(select(TablesUiLId.order_luiid))).scalar_one_or_none()

        for data in datas:
            
            cust_exists=await CustomersRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).get_by_id(customer_id=data['customer_id'])
            if not cust_exists['customer'] or len(cust_exists['customer'])<1:
                skipped_items.append(data)
                continue
            
            prod_exists=await ProductsRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).get_by_id(product_id=data['product_id'])
            if not prod_exists['product'] or len(prod_exists['product'])<1:
                skipped_items.append(data)
                continue
            
            distri_exists=await DistributorsRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).get_by_id(distributor_id=data['distributor_id'])
            if not distri_exists['distributors'] or len(distri_exists['distributors'])<1:
                skipped_items.append(data)
                continue
            
            last_ord_expiry_date=None
            if data['purchase_type']==PurchaseTypes.EXISTING_ADD_ON.value:
                last_order=await orders_obj.get_last_order(customer_id=cust_exists['customer']['id'],product_id=prod_exists['product']['id'])
                last_ord_expiry_date=last_order.get('last_order')['expiry_date']

            data['customer_id']=cust_exists['customer']['id']
            data['distributor_id']=distri_exists['distributors']['id']
            data['product_id']=prod_exists['product']['id']
            
            data['delivery_info']=DeliveryInfo(
                requested_date=pd.Timestamp(data['requested_date']).strftime("%Y-%m-%d"),
                delivery_date=pd.Timestamp(data['delivery_date']).strftime("%Y-%m-%d"),
                shipping_method=data['shipping_method'],
                payment_terms=data['payment_terms']
            )

            data['status_info']=StatusInfo(
                payment_status=data['payment_status'],
                invoice_status=data['invoice_status'],
                invoice_number=data['invoice_number'],
                invoice_date=pd.Timestamp(data['invoice_date']).strftime("%Y-%m-%d")
            )

            data['logistic_info']=LogisticsInfo(
                purchase_type=data['purchase_type'],
                renewal_type=data['renewal_type'],
                bill_to=data['bill_to'],
                distributor_type=data['distributor_type'],
                last_ord_expiry_date=last_ord_expiry_date
            )

            order_id:str=generate_uuid()
            cur_uiid=generate_ui_id(prefix=LUI_ID_ORDER_PREFIX,last_id=lui_id)
            lui_id=cur_uiid

            formatted_schema=AddOrderDbSchema(**data,id=order_id,ui_id=cur_uiid).model_dump(mode='json',exclude_unset=True,exclude_none=True)
            datas_toadd.append(Orders(**formatted_schema))
                
        ic(skipped_items,datas_toadd)
        return await orders_obj.add_bulk(datas=datas_toadd,lui_id=lui_id)
    

    @catch_errors
    async def update(self,data:UpdateOrderSchema):
        data_toupdate=data.model_dump(mode='json',exclude_none=True,exclude_unset=True)
        if not data_toupdate or len(data_toupdate)<1:
            return ErrorResponseTypDict(status_code=400,success=False,msg="Error : Updating Order",description="No valid fields to update provided")
        
        order_obj=OrdersRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id)

        cust_exists=await CustomersRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).get_by_id(customer_id=data.customer_id)
        if not cust_exists or len(cust_exists)<1:
            return ErrorResponseTypDict(status_code=400,success=False,msg="Error : Adding Order",description="Customer with the given id does not exist")
        
        prod_exists=await ProductsRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).get_by_id(product_id=data.product_id)
        if not prod_exists or len(prod_exists)<1:
            return ErrorResponseTypDict(status_code=400,success=False,msg="Error : Adding Order",description="Product with the given id does not exist")
        
        distri_exists=await DistributorsRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).get_by_id(distributor_id=data.distributor_id)
        if not distri_exists or len(distri_exists)<1:
            return ErrorResponseTypDict(status_code=400,success=False,msg="Error : Adding Order",description="Distributor with the given id does not exist")

        if data.logistic_info.get('purchase_type').value==PurchaseTypes.EXISTING_ADD_ON.value:
            last_order=await order_obj.get_last_order(customer_id=cust_exists['customer']['id'],product_id=prod_exists['product']['id'])
            last_ord_expiry_date=last_order.get('last_order')['expiry_date']
            ic(last_ord_expiry_date)
            data_toupdate['logistic_info']['last_ord_expiry_date']=last_ord_expiry_date

        return await OrdersRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).update(data=UpdateOrderDbSchema(**data_toupdate))


    @catch_errors    
    async def delete(self,order_id:str,customer_id:str,soft_delete:bool=True):
        return await OrdersRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).delete(order_id=order_id,customer_id=customer_id,soft_delete=soft_delete)
    
    @catch_errors  
    async def recover(self,order_id:str,customer_id:str):
        return await OrdersRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).recover(order_id=order_id,customer_id=customer_id)

    @catch_errors
    async def get(self,filter:OrderFilterSchema,cursor:int=1,limit:int=10,query:str='',include_deleted:Optional[bool]=False,):
        return await OrdersRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).get(cursor=cursor,limit=limit,query=query,include_deleted=include_deleted,filter=filter)
    
    @catch_errors
    async def search(self,query:str):
        return await OrdersRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).search(query=query)

    @catch_errors  
    async def get_by_id(self,order_id:str):
        return await OrdersRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).get_by_id(order_id=order_id)
        
    @catch_errors
    async def get_by_customer_id(self,customer_id:str,cursor:int,limit:int):
        return await OrdersRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).get_by_customer_id(customer_id=customer_id,cursor=cursor,limit=limit)
    
    @catch_errors
    async def get_last_order(self,customer_id:str,product_id:str):
        return await OrdersRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).get_last_order(customer_id=customer_id,product_id=product_id)



