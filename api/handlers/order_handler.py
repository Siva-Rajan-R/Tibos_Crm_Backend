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
from core.utils.discount_validator import validate_discount
from core.data_formats.enums.filters_enum import OrdersFilters
from core.data_formats.enums.common_enums import ImportExportTypeEnum
from core.utils.excel_data_extractor import extract_excel_data
from models.import_export_models.excel_headings_mapper import ORDERS_MAPPER
from fastapi import UploadFile

class HandleOrdersRequest:
    def __init__(self,session:AsyncSession,user_role:UserRoles,cur_user_id:str):
        self.session=session
        self.user_role=user_role
        self.cur_user_id=cur_user_id

        # if isinstance(self.user_role,UserRoles):
        #     self.user_role=self.user_role.value

        # if self.user_role==UserRoles.USER.value:
        #     raise HTTPException(
        #         status_code=401,
        #         detail=ErrorResponseTypDict(
        #             msg="Error : ",
        #             description="Insufficient permission",
        #             status_code=401,
        #             success=False
        #         ).model_dump(mode='json')
        #     )

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
                ).model_dump(mode='json')
            )

        if data.discount and validate_discount(value=data.discount) is None:
            raise HTTPException(
                status_code=400,
                detail=ErrorResponseTypDict(
                    status_code=400,
                    success=False,
                    msg="Error : Creating Order",
                    description="Invalid discount format"
                ).model_dump(mode='json')
            )
        
        if data.vendor_commision and validate_discount(value=data.vendor_commision) is None:
            raise HTTPException(
                status_code=400,
                detail=ErrorResponseTypDict(
                    status_code=400,
                    success=False,
                    msg="Error : Creating Order",
                    description="Invalid vendor discount format"
                ).model_dump(mode='json')
            )
        
        res=await OrdersService(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).add(data=data)
        if not res or isinstance(res,ErrorResponseTypDict):
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
        return SuccessResponseTypDict(
            detail=BaseResponseTypDict(
                status_code=200,
                success=True,
                msg="Order created successfully"
            )
        )
    
    @catch_errors
    async def add_bulk(self,type:ImportExportTypeEnum,file:UploadFile):
        if type.value==ImportExportTypeEnum.EXCEL.value:
            datas_toadd=extract_excel_data(excel_file=file.file,headings_mapper=ORDERS_MAPPER)
            if not datas_toadd or len(datas_toadd)<=0:
                raise HTTPException(
                    status_code=400,
                    detail=ErrorResponseTypDict(
                        status_code=400,
                        success=False,
                        msg="Adding bulk order",
                        description="Invalid columns or insufficent datas to add"
                    ).model_dump(mode='json')
                )
            res=await OrdersService(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).add_bulk(datas=datas_toadd)
            if res:
                return SuccessResponseTypDict(
                    detail=BaseResponseTypDict(
                        status_code=200,
                        msg="Orders added successfully",
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
                ).model_dump(mode='json')
            )
        
        if data.discount and validate_discount(value=data.discount) is None:
            raise HTTPException(
                status_code=400,
                detail=ErrorResponseTypDict(
                    status_code=400,
                    success=False,
                    msg="Error : Creating Order",
                    description="Invalid discount format"
                ).model_dump(mode='json')
            )
        
        if data.vendor_commision and validate_discount(value=data.vendor_commision) is None:
            raise HTTPException(
                status_code=400,
                detail=ErrorResponseTypDict(
                    status_code=400,
                    success=False,
                    msg="Error : Creating Order",
                    description="Invalid vendor discount format"
                ).model_dump(mode='json')
            )
        
        res = await OrdersService(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).update(data=data)
        if not res or isinstance(res,ErrorResponseTypDict):
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
        if not res or isinstance(res,ErrorResponseTypDict):
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
        if not res or isinstance(res,ErrorResponseTypDict):
            detail:ErrorResponseTypDict=ErrorResponseTypDict(
                    status_code=400,
                    msg="Error : Recovering Order",
                    description="A Unknown Error, Please Try Again Later!",
                    success=False
                ) if not isinstance(res,ErrorResponseTypDict) else res
            
            raise HTTPException(
                status_code=detail.status_code,
                detail=detail.model_dump(mode='json')
            )
        
        return SuccessResponseTypDict(
            detail=BaseResponseTypDict(
                status_code=200,
                success=True,
                msg="Order recovered successfully"
            )
        )

    @catch_errors
    async def get(self,cursor:int=1,limit:int=10,query:str='',filter:OrdersFilters=None):
        if cursor is None:
            raise HTTPException(
                status_code=400,
                detail=ErrorResponseTypDict(
                    status_code=400,
                    description="No more datas found for orders",
                    msg="Error : fetching orders",
                    success=False
                )
            )
        return await OrdersService(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).get(cursor=cursor,limit=limit,query=query,filter=filter)
    
    @catch_errors
    async def search(self,query:str):
        return await OrdersService(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).search(query=query)

    @catch_errors  
    async def get_by_id(self,order_id:str):
        return await OrdersService(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).get_by_id(order_id=order_id)
        
    @catch_errors
    async def get_by_customer_id(self,customer_id:str,offset:int,limit:int):
        return await OrdersService(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).get_by_customer_id(customer_id=customer_id,offset=offset,limit=limit)



