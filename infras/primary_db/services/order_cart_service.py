from typing import cast,List
from models.service_models.base_model import BaseServiceModel
from ..models.order import CartOrders,OrdersPaymentInvoiceInfo,CartOrdersProduct
from ..models.product import Products
from ..models.customer import Customers
from ..models.distributor import Distributors
from core.utils.uuid_generator import generate_uuid
from sqlalchemy import Numeric, select,delete,update,or_,func,String,cast,case,and_,Date,desc,text,exists
from sqlalchemy.ext.asyncio import AsyncSession
from icecream import ic
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import literal,true
from core.data_formats.enums.user_enums import UserRoles
from core.data_formats.enums.order_enums import PaymentStatus,InvoiceStatus,PurchaseTypes,OrderFilterRevenueEnum,ActivationStatusEnum
from schemas.db_schemas.order import AddCartOrderDbSchema,UpdateCartOrderProductDbSchema,UpdateCartOrderDbSchema,AddCartOrderProductDbSchema
from schemas.request_schemas.order import AddCartOrderSchema,UpdateCartOrderSchema,AddCartOrderProductSchema,UpdateCartOrderProductSchema
from core.decorators.db_session_handler_dec import start_db_transaction
from math import ceil
from ..models.user import Users
from models.response_models.req_res_models import SuccessResponseTypDict,BaseResponseTypDict,ErrorResponseTypDict
from core.utils.discount_validator import validate_discount
from ..models.ui_id import TablesUiLId
from schemas.request_schemas.order import OrderFilterSchema
from datetime import datetime,timedelta
from core.constants import DEFAULT_ADDON_YEAR
from typing import Optional,Literal
from core.utils.ui_id_generator import generate_ui_id
from core.data_formats.enums.order_enums import OrderFilterDateByEnum
from ..repos.order_cart_repo import OrdersCartRepo
from core.constants import LUI_ID_CART_ORDER_PREFIX
from ..calculations import distri_final_price,customer_final_price,profit_loss_price,customer_tot_price,distributor_tot_price,vendor_disc_price,distri_additi_price,distri_disc_price,remaining_days,last_order_delivery_date,expiry_date,distri_discount,pending_amount,total_paid_amount,customer_amount_with_gst



class OrdersCartService(BaseServiceModel):
    def __init__(self,session:AsyncSession,user_role:UserRoles,cur_user_id:str):
        self.session=session
        self.user_role=user_role
        self.cur_user_id=cur_user_id

    async def update(self, data:UpdateCartOrderSchema):
        order_data=UpdateCartOrderDbSchema(**data.model_dump(mode="json"))

        product_datas=[]

        for product in data.products:
            product_datas.append(
                product.model_dump(mode="json")
            )
        
        ic(product_datas)

        return await OrdersCartRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).update(order_data=order_data,products_data=product_datas)

    
    async def delete(self,order_id:str,soft_delete:bool=True):
        return await OrdersCartRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).delete(order_id=order_id,soft_delete=soft_delete)
    
    async def get_by_id(self, order_id:str):
        return await OrdersCartRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).get_by_id(order_id=order_id)
    
    async def search(self, *args, **kwargs):
        return await super().search(*args, **kwargs)

    
    async def add(self,data:AddCartOrderSchema):
        order_id:str=generate_uuid()
        product_datas=[]
        for product in data.products:
            product_datas.append(
                CartOrdersProduct(**product.model_dump(mode='json'),order_id=order_id,id=generate_uuid())
            )
        ic(product_datas)

        lui_id:str=(await self.session.execute(select(TablesUiLId.cart_order_luiid))).scalar_one_or_none()
        ic(lui_id)
        cur_uiid=generate_ui_id(prefix=LUI_ID_CART_ORDER_PREFIX,last_id=lui_id)
        ic(cur_uiid)
        order_data=AddCartOrderDbSchema(
            id=order_id,
            ui_id=cur_uiid,
            **data.model_dump(mode="json",exclude=['products'])
        )
        
        res=await OrdersCartRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).add(order_data=order_data,product_datas=product_datas)
        return res


    async def get(
        self,
        filter: Optional[OrderFilterSchema]=OrderFilterSchema(),
        cursor: int = 1,
        limit: int = 10,
        query: str = '',
        include_deleted: bool = False,
        in_search:List=[]
    ):

        res=await OrdersCartRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).get(filter=filter,cursor=cursor,limit=limit,query=query,include_deleted=include_deleted,in_search=in_search)

        return res

    




