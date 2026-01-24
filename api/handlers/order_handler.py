from infras.primary_db.services.order_service import OrdersService
from sqlalchemy import select,delete,update,or_,func,String
from sqlalchemy.ext.asyncio import AsyncSession
from icecream import ic
from core.data_formats.enums.common_enums import UserRoles
from core.data_formats.enums.pg_enums import PaymentStatus,InvoiceStatus
from core.data_formats.typed_dicts.pg_dict import DeliveryInfo
from schemas.db_schemas.order import AddOrderDbSchema,UpdateOrderDbSchema
from schemas.request_schemas.order import AddOrderSchema,UpdateOrderSchema,RecoverOrderSchema
from core.decorators.error_handler_dec import catch_errors
from math import ceil
from . import HTTPException,ErrorResponseTypDict,SuccessResponseTypDict,BaseResponseTypDict



class HandleOrdersRequest:
    def __init__(self,session:AsyncSession,user_role:UserRoles,cur_user_id:str):
        self.session=session
        self.user_role=user_role
        self.cur_user_id=cur_user_id

        if isinstance(self.user_role,UserRoles):
            self.user_role=self.user_role.value

        if self.user_role==UserRoles.USER.value:
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
        if data.invoice_status.value==InvoiceStatus.COMPLETED.value and ((not data.invoice_number or len(data.invoice_number)<1 or (not data.invoice_date))):
            raise HTTPException(
                status_code=400,
                detail=ErrorResponseTypDict(
                    status_code=400,
                    success=False,
                    msg="Error : Creading Order",
                    description="Enter a vaid Inovice number or Date"
                )
            )
        
        res=await OrdersService(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).add(data=data)
        if not res:
            raise HTTPException(
                status_code=400,
                detail=ErrorResponseTypDict(
                    status_code=400,
                    msg="Error : Creating Order",
                    description="A Order or Account already exists or Invalid inputs !"
                )
            )
        return SuccessResponseTypDict(
            detail=BaseResponseTypDict(
                status_code=200,
                success=True,
                msg="Order created successfully"
            )
        )
    
    @catch_errors
    async def update(self,data:UpdateOrderSchema):
        if data.invoice_status.value==InvoiceStatus.COMPLETED.value and ((not data.invoice_number or len(data.invoice_number)<1 or (not data.invoice_date))):
            raise HTTPException(
                status_code=400,
                detail=ErrorResponseTypDict(
                    status_code=400,
                    success=False,
                    msg="Error : Creading Order",
                    description="Enter a vaid Inovice number or Date"
                )
            )
        res = await OrdersService(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).update(data=data)
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
    async def delete(self,order_id:str,customer_id:str,soft_delete:bool=True):
        res = await OrdersService(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).delete(order_id=order_id,customer_id=customer_id,soft_delete=soft_delete)
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
    async def recover(self,data:RecoverOrderSchema): 
        res = await OrdersService(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).recover(order_id=data.order_id,customer_id=data.customer_id)
        if not res:
            raise HTTPException(
                status_code=400,
                detail=ErrorResponseTypDict(
                    status_code=400,
                    success=False,
                    msg="Error : Recovering order",
                    description="Invalid user input"
                )
            )
        
        return SuccessResponseTypDict(
            detail=BaseResponseTypDict(
                status_code=200,
                success=True,
                msg="Order recovered successfully"
            )
        )

    @catch_errors
    async def get(self,offset:int=1,limit:int=10,query:str=''):
        return await OrdersService(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).get(offset=offset,limit=limit,query=query)
    
    @catch_errors
    async def search(self,query:str):
        return await OrdersService(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).search(query=query)

    @catch_errors  
    async def get_by_id(self,order_id:str):
        return await OrdersService(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).get_by_id(order_id=order_id)
        
    @catch_errors
    async def get_by_customer_id(self,customer_id:str,offset:int,limit:int):
        return await OrdersService(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).get_by_customer_id(customer_id=customer_id,offset=offset,limit=limit)



