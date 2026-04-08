from typing import cast,List
from core.utils.uuid_generator import generate_uuid
from sqlalchemy import Numeric, select,delete,update,or_,func,String,cast,case,and_,Date,desc,text,exists
from sqlalchemy.ext.asyncio import AsyncSession
from icecream import ic
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import literal,true
from core.data_formats.enums.user_enums import UserRoles
from core.data_formats.enums.order_enums import PaymentStatus,InvoiceStatus,PurchaseTypes,OrderFilterRevenueEnum,ActivationStatusEnum
from schemas.db_schemas.order import AddCartOrderDbSchema,UpdateCartOrderProductDbSchema,UpdateOrderDbSchema,AddCartOrderProductDbSchema
from schemas.request_schemas.order import AddCartOrderSchema,UpdateCartOrderSchema,AddCartOrderProductSchema,UpdateCartOrderProductSchema
from core.decorators.db_session_handler_dec import start_db_transaction
from math import ceil
from models.response_models.req_res_models import SuccessResponseTypDict,BaseResponseTypDict,ErrorResponseTypDict
from core.utils.discount_validator import validate_discount
from schemas.request_schemas.order import OrderFilterSchema
from datetime import datetime,timedelta
from core.constants import DEFAULT_ADDON_YEAR
from typing import Optional,Literal
from core.data_formats.enums.order_enums import OrderFilterDateByEnum
from infras.primary_db.services.order_cart_service import OrdersCartService



class HandleOrderCartRequest:
    def __init__(self,session:AsyncSession,user_role:UserRoles,cur_user_id:str):
        self.session=session
        self.user_role=user_role
        self.cur_user_id=cur_user_id


    async def add(self,data:AddCartOrderSchema):
        res=await OrdersCartService(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).add(data=data)
        return res


    async def get(
        self,
        filter: Optional[OrderFilterSchema]=OrderFilterSchema(),
        cursor: int = 1,
        limit: int = 10,
        query: str = '',
        include_deleted: bool = False,
    ):

        res=await OrdersCartService(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).get(filter=filter,cursor=cursor,limit=limit,query=query,include_deleted=include_deleted,in_search=[])
        return res
