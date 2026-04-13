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
from schemas.request_schemas.order import AddCartOrderSchema,UpdateCartOrderSchema,AddCartOrderProductSchema,UpdateCartOrderProductSchema,UpdateCartOrderQuantitySchema
from core.decorators.db_session_handler_dec import start_db_transaction
from math import ceil
from models.response_models.req_res_models import SuccessResponseTypDict,BaseResponseTypDict,ErrorResponseTypDict
from core.utils.discount_validator import validate_discount
from schemas.request_schemas.order import OrderFilterSchema
from datetime import datetime,timedelta
from core.constants import DEFAULT_ADDON_YEAR
from typing import Optional,Literal
from core.data_formats.enums.order_enums import OrderFilterDateByEnum,RenewalTypes,PurchaseTypes
from infras.primary_db.services.order_cart_service import OrdersCartService
from fastapi import HTTPException



class HandleOrderCartRequest:
    def __init__(self,session:AsyncSession,user_role:UserRoles,cur_user_id:str):
        self.session=session
        self.user_role=user_role
        self.cur_user_id=cur_user_id


    async def add(self,data:AddCartOrderSchema,is_renewal:bool=False):
        if is_renewal:
            data.logistic_info['purchase_type']=PurchaseTypes.EXISTING_RENEWAL.value
        ic(data.logistic_info)
        res=await OrdersCartService(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).add(data=data)
        if res:
            return SuccessResponseTypDict(
                detail=BaseResponseTypDict(
                    status_code=201,
                    msg="Orders Created successfully",
                    success=True
                )
            )
            
        detail:ErrorResponseTypDict=ErrorResponseTypDict(
                status_code=400,
                msg="Error : Creating Order",
                description="A Unknown Error, Please Try Again Later!",
                success=False
            ) if not isinstance(res,ErrorResponseTypDict) else res
        
        raise HTTPException(
            status_code=detail.status_code,
            detail=detail.model_dump(mode='json')
        )
        


    async def update(self,data:UpdateCartOrderSchema):
        res=await OrdersCartService(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).update(data=data)
        if res:
            return SuccessResponseTypDict(
                detail=BaseResponseTypDict(
                    status_code=200,
                    msg="Orders updated successfully",
                    success=True
                )
            )
            
        detail:ErrorResponseTypDict=ErrorResponseTypDict(
                status_code=400,
                msg="Error : Updating Order",
                description="A Unknown Error, Please Try Again Later!",
                success=False
            ) if not isinstance(res,ErrorResponseTypDict) else res
        
        raise HTTPException(
            status_code=detail.status_code,
            detail=detail.model_dump(mode='json')
        )
    
    async def delete(self,order_id:str,soft_delete:bool=True):
        res=await OrdersCartService(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).delete(order_id=order_id,soft_delete=soft_delete)
        if res:
            return SuccessResponseTypDict(
                detail=BaseResponseTypDict(
                    status_code=200,
                    msg="Orders deleted successfully",
                    success=True
                )
            )
            
        detail:ErrorResponseTypDict=ErrorResponseTypDict(
                status_code=400,
                msg="Error : Deleting Order",
                description="A Unknown Error, Please Try Again Later!",
                success=False
            ) if not isinstance(res,ErrorResponseTypDict) else res
        
        raise HTTPException(
            status_code=detail.status_code,
            detail=detail.model_dump(mode='json')
        )
    
    async def update_qty(self,data:UpdateCartOrderQuantitySchema):
        res=await OrdersCartService(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).update_qty(data=data)
        return res
    
    async def getby_id(self,order_id:str):
        res=await OrdersCartService(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).get_by_id(order_id=order_id)
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
