from fastapi import Depends,APIRouter,Query,Form,UploadFile,Query,File,Request,BackgroundTasks,HTTPException
from schemas.request_schemas.order import AddOrderSchema,UpdateOrderSchema,RecoverOrderSchema,OrderBulkDeleteSchema,OrderTrackingReportSchema,PaymentPendingReportSchema,DistributorProjectionReportSchema
from infras.primary_db.main import get_pg_db_session,AsyncSession
from api.dependencies.token_verification import verify_user
from ..handlers.order_handler import HandleOrdersRequest
from typing import Optional,List
from core.data_formats.enums.dd_enums import ImportExportTypeEnum
from schemas.request_schemas.order import OrderFilterSchema
from models.response_models.req_res_models import SuccessResponseTypDict,BaseResponseTypDict
from core.utils.export_func import create_excel_export
from infras.primary_db.repos.order_repo import (
    OrdersRepo, 
    OrderTrackingReportRepo, 
    PaymentPendingReportRepo, 
    DistributorProjectionReportRepo,
    PendingInvoiceReportRepo,
    ActivationAlertReportRepo
)
from core.data_formats.enums.user_enums import UserRoles
from models.import_export_models.exports.excel_headings_mapper import (
    ORDERS_MAPPER, 
    ORDER_TRACKING_REPORT_MAPPER, 
    PAYMENT_PENDING_REPORT_MAPPER, 
    DISTRIBUTOR_PROJECTION_REPORT_MAPPER,
    PENDING_INVOICE_REPORT_MAPPER,
    ACTIVATION_ALERT_REPORT_MAPPER
)
from schemas.request_schemas.export import ExportFields
from tasks.arq_tasks.enqueues.report import enqueue_excel_report_job
from pydantic import EmailStr
from icecream import ic





router=APIRouter(
    tags=['Order Crud'],
    prefix='/order'
)


@router.post('')
async def add(data:AddOrderSchema,request:Request,bgt:BackgroundTasks,user:dict=Depends(verify_user),session:AsyncSession=Depends(get_pg_db_session)):
    return await HandleOrdersRequest(
        session=session,
        user_role=user['role'],
        cur_user_id=user['id']
    ).add(
        data=data,
        request=request,
        bgt=bgt
    )

@router.post('/bulk')
async def add_bulk(user:dict=Depends(verify_user),session:AsyncSession=Depends(get_pg_db_session),type:ImportExportTypeEnum=Form(...),file:UploadFile=File(...)):
    return await HandleOrdersRequest(
        session=session,
        user_role=user['role'],
        cur_user_id=user['id']
    ).add_bulk(type=type,file=file)


@router.put('')
async def update(data:UpdateOrderSchema,request:Request,bgt:BackgroundTasks,user:dict=Depends(verify_user),session:AsyncSession=Depends(get_pg_db_session)):
    return await HandleOrdersRequest(
        session=session,
        user_role=user['role'],
        cur_user_id=user['id']
    ).update(
        data=data,
        request=request,
        bgt=bgt
    )


@router.delete('/{customer_id}/{order_id}')
async def delete_order(customer_id:str,order_id:str,user:dict=Depends(verify_user),soft_delete:Optional[bool]=Query(True),session:AsyncSession=Depends(get_pg_db_session)):
    return await HandleOrdersRequest(
        session=session,
        user_role=user['role'],
        cur_user_id=user['id']
    ).delete(
        customer_id=customer_id,
        order_id=order_id,
        soft_delete=soft_delete
    )

@router.post('/delete/bulk')
async def delete_order(data:OrderBulkDeleteSchema,user:dict=Depends(verify_user),soft_delete:Optional[bool]=Query(True),session:AsyncSession=Depends(get_pg_db_session)):
    return await HandleOrdersRequest(
        session=session,
        user_role=user['role'],
        cur_user_id=user['id']
    ).delete_bulk(
        data=data,
        soft_delete=soft_delete
    )



# @router.get('/testing')
# async def testing(q:str=Query(''),cursor:Optional[int]=Query(1),limit:Optional[int]=Query(10),user:dict=Depends(verify_user),session:AsyncSession=Depends(get_pg_db_session)):
#     return await HandleOrdersRequest(
#         session=session,
#         user_role=user['role'],
#         cur_user_id=user['id']
#     ).test(cursor=cursor,limit=limit,query=q)


@router.put('/recover')
async def recover_order(data:RecoverOrderSchema,user:dict=Depends(verify_user),session:AsyncSession=Depends(get_pg_db_session)):
    return await HandleOrdersRequest(
        session=session,
        user_role=user['role'],
        cur_user_id=user['id']
    ).recover(
        data=data
    )

@router.post('/export')
async def export(data:ExportFields,bgt:BackgroundTasks,user:dict=Depends(verify_user),session:AsyncSession=Depends(get_pg_db_session)):
    ic(data.filters)
    ic("Hello Hii")
    if user['role']!=UserRoles.SUPER_ADMIN.value:
        raise HTTPException(
            status_code=401,
            detail="Insufficient Permission"
        )
    
    user_email:EmailStr=user['email']
    if user_email.split('@')[-1].lower()!='tibos.in':
        raise HTTPException(
            status_code=401,
            detail="Invalid User for export, Please login with your organization mail"
        )
    
    await enqueue_excel_report_job(
        user_id=user['id'],
        kwargs={"filter":data.filters},
        emails_tosend=[user_email],
        custom_fields=data.fields,
        mapper=ORDERS_MAPPER,
        data_cls=OrdersRepo,
        data_key='orders',
        converter_name='orders',
        sheet_name="Orders",
        file_name='TibosCrmOrdersExport.xlsx',
        report_name="Tibos CRM Orders Report"
    )

    from infras.primary_db.services.activity_log_service import ActivityLogService
    await ActivityLogService(session, user['role'], user['id']).log_action(
        action="EXPORT",
        entity_type="ORDER",
        details={"fields_exported": data.fields}
    )

    return SuccessResponseTypDict(
        detail=BaseResponseTypDict(
            msg="Excel sheet generation started, It will be sended to ur email",
            status_code=200,
            success=True
        )
    )

@router.get('/export/fields')
async def export(bgt:BackgroundTasks,user:dict=Depends(verify_user)):

    if user['role']!=UserRoles.SUPER_ADMIN.value:
        raise HTTPException(
            status_code=401,
            detail="Insufficient Permission"
        )
    fields=list(ORDERS_MAPPER.values())
    return SuccessResponseTypDict(
        detail=BaseResponseTypDict(
            msg="Export Fields fetched successfully",
            status_code=200,
            success=True
        ),
        data=fields
    )

@router.post('/get')
async def get_all_order(filters:OrderFilterSchema,q:str=Query(''),cursor:Optional[int]=Query(1),limit:Optional[int]=Query(10),active:bool=False,user:dict=Depends(verify_user),session:AsyncSession=Depends(get_pg_db_session)):
    return await HandleOrdersRequest(
        session=session,
        user_role=user['role'],
        cur_user_id=user['id']
    ).get(cursor=cursor,limit=limit,query=q,filter=filters,active=active)


@router.get('/search')
async def get_search_order(q:str=Query(...),user:dict=Depends(verify_user),session:AsyncSession=Depends(get_pg_db_session)):
    return await HandleOrdersRequest(
        session=session,
        user_role=user['role'],
        cur_user_id=user['id']
    ).search(query=q)


@router.get('/{order_id}')
async def get_order_by_order_id(order_id:str,user:dict=Depends(verify_user),session:AsyncSession=Depends(get_pg_db_session)):
    return await HandleOrdersRequest(
        session=session,
        user_role=user['role'],
        cur_user_id=user['id']
    ).get_by_id(order_id=order_id)



@router.get('/customer/{customer_id}')
async def get_order_by_customer_id(customer_id:str,user:dict=Depends(verify_user),cursor:Optional[int]=Query(1),limit:Optional[int]=Query(10),session:AsyncSession=Depends(get_pg_db_session)):
    return await HandleOrdersRequest(
        session=session,
        user_role=user['role'],
        cur_user_id=user['id']
    ).get_by_customer_id(customer_id=customer_id,cursor=cursor,limit=limit)

@router.get('/last/{customer_id}/{product_id}')
async def get_last_order_date(customer_id:str,product_id:str,user:dict=Depends(verify_user),session:AsyncSession=Depends(get_pg_db_session)):
    return await HandleOrdersRequest(
        session=session,
        user_role=user['role'],
        cur_user_id=user['id']
    ).get_last_order(customer_id=customer_id,product_id=product_id)


@router.get('/distributor-pay/by/{customer_id}')
async def get_cust_distri(customer_id: str,user:dict=Depends(verify_user),session:AsyncSession=Depends(get_pg_db_session)):
        return await HandleOrdersRequest(session=session,user_role=user['role'],cur_user_id=user['id']).get_cust_distri(customer_id=customer_id)

@router.get('/distributor-pay/by/{customer_id}/{distributor_id}') 
async def get_cust_prod(customer_id:str,distributor_id:str,user:dict=Depends(verify_user),session:AsyncSession=Depends(get_pg_db_session)):
    return await HandleOrdersRequest(session=session,user_role=user['role'],cur_user_id=user['id']).get_cust_prod(customer_id=customer_id,distributor_id=distributor_id)

@router.get('/distributor-pay/by/{customer_id}/{distributor_id}/{product_id}')
async def get_cust_order(customer_id:str,distributor_id:str,product_id:str,user:dict=Depends(verify_user),session:AsyncSession=Depends(get_pg_db_session)):
    return await HandleOrdersRequest(session=session,user_role=user['role'],cur_user_id=user['id']).get_cust_order(customer_id=customer_id,distributor_id=distributor_id,product_id=product_id)

@router.post('/report/tracking')
async def get_order_tracking_report(data:OrderTrackingReportSchema,user:dict=Depends(verify_user),session:AsyncSession=Depends(get_pg_db_session)):
    return await HandleOrdersRequest(
        session=session,
        user_role=user['role'],
        cur_user_id=user['id']
    ).get_order_tracking_report(data=data)


@router.post('/report/tracking/export')
async def export_tracking_report(data:OrderTrackingReportSchema,user:dict=Depends(verify_user),session:AsyncSession=Depends(get_pg_db_session)):

    if user['role']!=UserRoles.SUPER_ADMIN.value:
        raise HTTPException(
            status_code=401,
            detail="Insufficient Permission"
        )
    
    user_email:EmailStr=user['email']
    if user_email.split('@')[-1].lower()!='tibos.in':
        raise HTTPException(
            status_code=401,
            detail="Invalid User for export, Please login with your organization mail"
        )
    
    await enqueue_excel_report_job(
        user_id=user['id'],
        kwargs={
            "from_date": data.from_date,
            "to_date": data.to_date,
            "owner_name": data.owner_name,
            "date_by": data.date_by
        },
        emails_tosend=[user_email],
        mapper=ORDER_TRACKING_REPORT_MAPPER,
        data_cls=OrderTrackingReportRepo,
        data_key='owners',
        converter_name='TRACKING_REPORT',
        sheet_name="Order Tracking Report",
        file_name='TibosCrmOrderTrackingReport.xlsx',
        report_name="Order Tracking Report"
    )

    from infras.primary_db.services.activity_log_service import ActivityLogService
    await ActivityLogService(session, user['role'], user['id']).log_action(
        action="EXPORT",
        entity_type="ORDER_TRACKING_REPORT",
        details={}
    )

    return SuccessResponseTypDict(
        detail=BaseResponseTypDict(
            msg="Excel sheet generation started, It will be sended to ur email",
            status_code=200,
            success=True
        )
    )

@router.get('/report/tracking/export/fields')
async def get_tracking_report_export_fields(user:dict=Depends(verify_user)):

    if user['role']!=UserRoles.SUPER_ADMIN.value:
        raise HTTPException(
            status_code=401,
            detail="Insufficient Permission"
        )
    fields=list(ORDER_TRACKING_REPORT_MAPPER.values())
    return SuccessResponseTypDict(
        detail=BaseResponseTypDict(
            msg="Export Fields fetched successfully",
            status_code=200,
            success=True
        ),
        data=fields
    )


@router.post('/report/payment-pending')
async def get_payment_pending_report(data:PaymentPendingReportSchema,user:dict=Depends(verify_user),session:AsyncSession=Depends(get_pg_db_session)):
    return await HandleOrdersRequest(
        session=session,
        user_role=user['role'],
        cur_user_id=user['id']
    ).get_payment_pending_report(data=data)


@router.post('/report/payment-pending/export')
async def export_payment_pending_report(data:PaymentPendingReportSchema,user:dict=Depends(verify_user),session:AsyncSession=Depends(get_pg_db_session)):

    if user['role']!=UserRoles.SUPER_ADMIN.value:
        raise HTTPException(
            status_code=401,
            detail="Insufficient Permission"
        )
    
    user_email:EmailStr=user['email']
    if user_email.split('@')[-1].lower()!='tibos.in':
        raise HTTPException(
            status_code=401,
            detail="Invalid User for export, Please login with your organization mail"
        )
    
    await enqueue_excel_report_job(
        user_id=user['id'],
        kwargs={
            "from_date": data.from_date,
            "to_date": data.to_date,
            "owner_name": data.owner_name,
            "min_days_pending": data.min_days_pending,
            "date_by": data.date_by
        },
        emails_tosend=[user_email],
        mapper=PAYMENT_PENDING_REPORT_MAPPER,
        data_cls=PaymentPendingReportRepo,
        data_key='owners',
        converter_name='TRACKING_REPORT',
        sheet_name="Payment Pending Report",
        file_name='TibosCrmPaymentPendingReport.xlsx',
        report_name="Payment Pending Report"
    )

    from infras.primary_db.services.activity_log_service import ActivityLogService
    await ActivityLogService(session, user['role'], user['id']).log_action(
        action="EXPORT",
        entity_type="ORDER_PAYMENT_PENDING_REPORT",
        details={}
    )

    return SuccessResponseTypDict(
        detail=BaseResponseTypDict(
            msg="Excel sheet generation started, It will be sended to ur email",
            status_code=200,
            success=True
        )
    )


@router.get('/report/payment-pending/export/fields')
async def get_payment_pending_export_fields(user:dict=Depends(verify_user)):

    if user['role']!=UserRoles.SUPER_ADMIN.value:
        raise HTTPException(
            status_code=401,
            detail="Insufficient Permission"
        )
    fields=list(PAYMENT_PENDING_REPORT_MAPPER.values())
    return SuccessResponseTypDict(
        detail=BaseResponseTypDict(
            msg="Export Fields fetched successfully",
            status_code=200,
            success=True
        ),
        data=fields
    )


@router.post('/report/distributor-projection')
async def get_distributor_projection_report(data:DistributorProjectionReportSchema,user:dict=Depends(verify_user),session:AsyncSession=Depends(get_pg_db_session)):
    return await HandleOrdersRequest(
        session=session,
        user_role=user['role'],
        cur_user_id=user['id']
    ).get_distributor_projection_report(data=data)

@router.post('/report/distributor-projection/export')
async def export_distributor_projection_report(data:DistributorProjectionReportSchema,user:dict=Depends(verify_user),session:AsyncSession=Depends(get_pg_db_session)):
    if user['role']!=UserRoles.SUPER_ADMIN.value:
        raise HTTPException(
            status_code=401,
            detail="Insufficient Permission"
        )
    
    user_email:EmailStr=user['email']
    if user_email.split('@')[-1].lower()!='tibos.in':
        raise HTTPException(
            status_code=401,
            detail="Invalid User for export, Please login with your organization mail"
        )
    
    await enqueue_excel_report_job(
        user_id=user['id'],
        kwargs={
            "distributor_id": data.distributor_id,
            "from_date": data.from_date,
            "to_date": data.to_date,
            "date_by": data.date_by.value if hasattr(data.date_by, 'value') else data.date_by
        },
        emails_tosend=[user_email],
        mapper=DISTRIBUTOR_PROJECTION_REPORT_MAPPER,
        data_cls=DistributorProjectionReportRepo,
        data_key='rows',
        converter_name='PROJECTION_REPORT',
        sheet_name="Distributor Projection",
        file_name='TibosCrmDistributorProjectionReport.xlsx',
        report_name="Distributor Projection Report"
    )

    from infras.primary_db.services.activity_log_service import ActivityLogService
    await ActivityLogService(session, user['role'], user['id']).log_action(
        action="EXPORT",
        entity_type="ORDER_DISTRIBUTOR_PROJECTION_REPORT",
        details={}
    )

    return SuccessResponseTypDict(
        detail=BaseResponseTypDict(
            msg="Excel sheet generation started, It will be sended to ur email",
            status_code=200,
            success=True
        )
    )

@router.get('/report/distributor-projection/export/fields')
async def get_distributor_projection_export_fields(user:dict=Depends(verify_user)):
    if user['role']!=UserRoles.SUPER_ADMIN.value:
        raise HTTPException(
            status_code=401,
            detail="Insufficient Permission"
        )
    fields=list(DISTRIBUTOR_PROJECTION_REPORT_MAPPER.values())
    return SuccessResponseTypDict(
        detail=BaseResponseTypDict(
            msg="Export Fields fetched successfully",
            status_code=200,
            success=True
        ),
        data=fields
    )

@router.get('/report/pending-invoices')
async def get_pending_invoice_alert(days_threshold: Optional[int] = Query(None), user:dict=Depends(verify_user),session:AsyncSession=Depends(get_pg_db_session)):
    return await HandleOrdersRequest(
        session=session,
        user_role=user['role'],
        cur_user_id=user['id']
    ).get_pending_invoice_alert(days_threshold=days_threshold)

@router.get('/report/activation-alerts')
async def get_activation_date_alert(days_before: Optional[int] = Query(None), days_after: Optional[int] = Query(None), user:dict=Depends(verify_user),session:AsyncSession=Depends(get_pg_db_session)):
    return await HandleOrdersRequest(
        session=session,
        user_role=user['role'],
        cur_user_id=user['id']
    ).get_activation_date_alert(days_before=days_before, days_after=days_after)

@router.post('/report/pending-invoices/export')
async def export_pending_invoice_report(days_threshold: Optional[int] = Query(0), user:dict=Depends(verify_user),session:AsyncSession=Depends(get_pg_db_session)):
    if user['role']!=UserRoles.SUPER_ADMIN.value:
        raise HTTPException(status_code=401, detail="Insufficient Permission")
    
    user_email:EmailStr=user['email']
    if user_email.split('@')[-1].lower()!='tibos.in':
        raise HTTPException(status_code=401, detail="Invalid User for export")
    
    await enqueue_excel_report_job(
        user_id=user['id'],
        kwargs={"days_threshold": days_threshold},
        emails_tosend=[user_email],
        mapper=PENDING_INVOICE_REPORT_MAPPER,
        data_cls=PendingInvoiceReportRepo,
        data_key='data',
        converter_name='DEFAULT_JSON_CONVERTER',
        sheet_name="Pending Invoices",
        file_name='TibosCrmPendingInvoices.xlsx',
        report_name="Pending Invoices Report"
    )

    from infras.primary_db.services.activity_log_service import ActivityLogService
    await ActivityLogService(session, user['role'], user['id']).log_action(
        action="EXPORT",
        entity_type="ORDER_PENDING_INVOICES_REPORT",
        details={}
    )

    return SuccessResponseTypDict(detail=BaseResponseTypDict(msg="Export started", status_code=200, success=True))

@router.get('/report/pending-invoices/export/fields')
async def get_pending_invoice_export_fields(user:dict=Depends(verify_user)):
    if user['role']!=UserRoles.SUPER_ADMIN.value:
        raise HTTPException(status_code=401, detail="Insufficient Permission")
    return SuccessResponseTypDict(detail=BaseResponseTypDict(msg="Success", status_code=200, success=True), data=list(PENDING_INVOICE_REPORT_MAPPER.values()))

@router.post('/report/activation-alerts/export')
async def export_activation_alerts_report(days_before: int = 2, days_after: int = 2, user:dict=Depends(verify_user),session:AsyncSession=Depends(get_pg_db_session)):
    if user['role']!=UserRoles.SUPER_ADMIN.value:
        raise HTTPException(status_code=401, detail="Insufficient Permission")
    
    user_email:EmailStr=user['email']
    if user_email.split('@')[-1].lower()!='tibos.in':
        raise HTTPException(status_code=401, detail="Invalid User for export")
    
    await enqueue_excel_report_job(
        user_id=user['id'],
        kwargs={"days_before": days_before, "days_after": days_after},
        emails_tosend=[user_email],
        mapper=ACTIVATION_ALERT_REPORT_MAPPER,
        data_cls=ActivationAlertReportRepo,
        data_key='data',
        converter_name='DEFAULT_JSON_CONVERTER',
        sheet_name="Activation Alerts",
        file_name='TibosCrmActivationAlerts.xlsx',
        report_name="Activation Alerts Report"
    )

    from infras.primary_db.services.activity_log_service import ActivityLogService
    await ActivityLogService(session, user['role'], user['id']).log_action(
        action="EXPORT",
        entity_type="ORDER_ACTIVATION_ALERTS_REPORT",
        details={}
    )

    return SuccessResponseTypDict(detail=BaseResponseTypDict(msg="Export started", status_code=200, success=True))

@router.get('/report/activation-alerts/export/fields')
async def get_activation_alerts_export_fields(user:dict=Depends(verify_user)):
    if user['role']!=UserRoles.SUPER_ADMIN.value:
        raise HTTPException(status_code=401, detail="Insufficient Permission")
    return SuccessResponseTypDict(detail=BaseResponseTypDict(msg="Success", status_code=200, success=True), data=list(ACTIVATION_ALERT_REPORT_MAPPER.values()))
