from infras.primary_db.services.order_service import OrdersService
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
from . import HTTPException,ErrorResponseTypDict,SuccessResponseTypDict,BaseResponseTypDict



class HandleOrdersRequest:
    def __init__(self,session:AsyncSession,user_role:UserRoles):
        self.session=session
        self.user_role=user_role


        if self.user_role.value==UserRoles.USER.value:
            raise HTTPException(
                status_code=401,
                detail=ErrorResponseTypDict(
                    msg="Error : ",
                    description="Insufficient permission",
                    status_code=401,
                    success=False
                )
            )

    @catch_errors
    async def add(self,data:AddOrderSchema):
        res=await OrdersService(session=self.session,user_role=self.user_role).add(data=data)
        if res:
            return SuccessResponseTypDict(
            detail=BaseResponseTypDict(
                status_code=200,
                success=True,
                msg="Order created successfully"
            )
        )
    
    @catch_errors
    async def update(self,data:UpdateOrderSchema):
        res = await OrdersService(session=self.session,user_role=self.user_role).update(data=data)
        if not res:
            raise HTTPException(
                status_code=400,
                detail=ErrorResponseTypDict(
                    status_code=400,
                    success=False,
                    msg="Error : Updaing order",
                    description="Invalid user input"
                )
            )
        
        return SuccessResponseTypDict(
            detail=BaseResponseTypDict(
                status_code=200,
                success=True,
                msg="Order updated successfully"
            )
        )
        

    @catch_errors    
    async def delete(self,order_id:str,customer_id:str):
        res = await OrdersService(session=self.session,user_role=self.user_role).delete(order_id=order_id,customer_id=customer_id)
        if not res:
            raise HTTPException(
                status_code=400,
                detail=ErrorResponseTypDict(
                    status_code=400,
                    success=False,
                    msg="Error : Deleting order",
                    description="Invalid user input"
                )
            )
        
        return SuccessResponseTypDict(
            detail=BaseResponseTypDict(
                status_code=200,
                success=True,
                msg="Order deleted successfully"
            )
        )

    @catch_errors
    async def get(self,offset:int=1,limit:int=10,query:str=''):
        return await OrdersService(session=self.session,user_role=self.user_role).get(offset=offset,limit=limit,query=query)
    
    @catch_errors
    async def search(self,query:str):
        return await OrdersService(session=self.session,user_role=self.user_role).search(query=query)

    @catch_errors  
    async def get_by_id(self,order_id:str):
        return await OrdersService(session=self.session,user_role=self.user_role).get_by_id(order_id=order_id)
        
    @catch_errors
    async def get_by_customer_id(self,customer_id:str,offset:int,limit:int):
        return await OrdersService(session=self.session,user_role=self.user_role).get_by_customer_id(customer_id=customer_id,offset=offset,limit=limit)



