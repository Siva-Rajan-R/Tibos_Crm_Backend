from infras.primary_db.services.order_service import OrdersService
from sqlalchemy import select,delete,update,or_,func,String
from sqlalchemy.ext.asyncio import AsyncSession
from icecream import ic
from fastapi import Request,BackgroundTasks
from core.data_formats.enums.user_enums import UserRoles
from core.data_formats.enums.order_enums import PaymentStatus,InvoiceStatus
from core.data_formats.typed_dicts.order_typdict import DeliveryInfo
from schemas.db_schemas.order import AddOrderDbSchema,UpdateOrderDbSchema
from schemas.request_schemas.order import AddOrderSchema,UpdateOrderSchema,RecoverOrderSchema
from core.decorators.error_handler_dec import catch_errors
from math import ceil
from . import HTTPException,ErrorResponseTypDict,SuccessResponseTypDict,BaseResponseTypDict
from core.utils.discount_validator import validate_discount
from core.data_formats.enums.dd_enums import ImportExportTypeEnum,SettingsEnum
from core.utils.excel_data_extractor import extract_excel_data
from models.import_export_models.excel_headings_mapper import ORDERS_MAPPER
from fastapi import UploadFile
from schemas.request_schemas.order import OrderFilterSchema
from services.email_service import send_email
from templates.email.order import get_crm_order_email_content
from infras.primary_db.services.setting_service import SettingsService

class HandleOrdersRequest:
    def __init__(self,session:AsyncSession,user_role:UserRoles,cur_user_id:str):
        self.session=session
        self.user_role=user_role
        self.cur_user_id=cur_user_id

    @catch_errors
    async def add(self,data:AddOrderSchema,request:Request,bgt:BackgroundTasks):
        invoice_no=data.status_info.get('invoice_number')
        invoice_date=data.status_info.get('invoice_date')
        invoice_sts=data.status_info.get('invoice_status')
        if invoice_sts.value==InvoiceStatus.COMPLETED.value and ((not invoice_no or len(invoice_no)<1 or (not invoice_date))):
            raise HTTPException(
                status_code=400,
                detail=ErrorResponseTypDict(
                    status_code=400,
                    success=False,
                    msg="Error : Creading Order",
                    description="Enter a vaid Inovice number or Date"
                ).model_dump(mode='json')
            )

        if data.additional_discount and validate_discount(value=data.additional_discount) is None:
            raise HTTPException(
                status_code=400,
                detail=ErrorResponseTypDict(
                    status_code=400,
                    success=False,
                    msg="Error : Creating Order",
                    description="Invalid addtional discount format"
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
        if data.emailto_send_id:
            email_content=get_crm_order_email_content(customer_name="Tibos Testing",order_id="1234567899",company_name="TIBOS SOLUTIONS PVT LIMITED",total_amount=1000,items=[])
            bgt.add_task(send_email,client_ip=request.client.host,reciver_emails=['siva@tibos.in','siva967763@gmail.com'],subject="Order Confirmation",body=email_content,is_html=True,sender_email_id=data.emailto_send_id)
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
    async def update(self,data:UpdateOrderSchema,request:Request,bgt:BackgroundTasks):
        invoice_no=data.status_info.get('invoice_number')
        invoice_date=data.status_info.get('invoice_date')
        invoice_sts=data.status_info.get('invoice_status')
        if invoice_sts.value==InvoiceStatus.COMPLETED.value and ((not invoice_no or len(invoice_no)<1 or (not invoice_date))):
            raise HTTPException(
                status_code=400,
                detail=ErrorResponseTypDict(
                    status_code=400,
                    success=False,
                    msg="Error : Creading Order",
                    description="Enter a vaid Inovice number or Date"
                ).model_dump(mode='json')
            )
        
        if data.additional_discount and validate_discount(value=data.additional_discount) is None:
            raise HTTPException(
                status_code=400,
                detail=ErrorResponseTypDict(
                    status_code=400,
                    success=False,
                    msg="Error : Creating Order",
                    description="Invalid additional discount format"
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
        if data.emailto_send_id:
            email_content=get_crm_order_email_content(customer_name="Tibos Testing",order_id="1234567899",company_name="TIBOS SOLUTIONS PVT LIMITED",total_amount=1000,items=[])
            bgt.add_task(send_email,client_ip=request.client.host,reciver_emails=['siva@tibos.in','siva967763@gmail.com'],subject="Order Confirmation",body=email_content,is_html=True,sender_email_id=data.emailto_send_id)
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
    async def get(self,filter:OrderFilterSchema,cursor:int=1,limit:int=10,query:str=''):
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
    async def get_by_customer_id(self,customer_id:str,cursor:int,limit:int):
        return await OrdersService(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).get_by_customer_id(customer_id=customer_id,cursor=cursor,limit=limit)


    @catch_errors
    async def get_last_order(self,customer_id:str,product_id:str):
        return await OrdersService(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).get_last_order(customer_id=customer_id,product_id=product_id)
