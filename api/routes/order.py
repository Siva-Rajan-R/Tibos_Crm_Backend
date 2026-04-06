from fastapi import Depends,APIRouter,Query,Form,UploadFile,Query,File,Request,BackgroundTasks,HTTPException
from schemas.request_schemas.order import AddOrderSchema,UpdateOrderSchema,RecoverOrderSchema,OrderBulkDeleteSchema
from infras.primary_db.main import get_pg_db_session,AsyncSession
from api.dependencies.token_verification import verify_user
from ..handlers.order_handler import HandleOrdersRequest
from typing import Optional,List
from core.data_formats.enums.dd_enums import ImportExportTypeEnum
from schemas.request_schemas.order import OrderFilterSchema
from models.response_models.req_res_models import SuccessResponseTypDict,BaseResponseTypDict
from core.utils.export_func import create_excel_export
from infras.primary_db.repos.order_repo import OrdersRepo
from core.data_formats.enums.user_enums import UserRoles
from models.import_export_models.exports.excel_headings_mapper import ORDERS_MAPPER
from schemas.request_schemas.export import ExportFields
from tasks.arq_tasks.enqueues.report import enqueue_excel_report_job
from pydantic import EmailStr
from icecream import ic
from infras.primary_db.repos.order_repo import OrdersRepo





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
async def export(data:ExportFields,bgt:BackgroundTasks,user:dict=Depends(verify_user)):
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
async def get_all_order(filters:OrderFilterSchema,q:str=Query(''),cursor:Optional[int]=Query(1),limit:Optional[int]=Query(10),user:dict=Depends(verify_user),session:AsyncSession=Depends(get_pg_db_session)):
    return await HandleOrdersRequest(
        session=session,
        user_role=user['role'],
        cur_user_id=user['id']
    ).get(cursor=cursor,limit=limit,query=q,filter=filters)


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
    
