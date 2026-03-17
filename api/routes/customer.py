from fastapi import Depends,APIRouter,Query,File,UploadFile,Form,BackgroundTasks,HTTPException
from schemas.request_schemas.customer import AddCustomerSchema,UpdateCustomerSchema,RecoverCustomerSchema,ResponseSearch,FinalResponseModel
from infras.primary_db.main import get_pg_db_session,AsyncSession
from api.dependencies.token_verification import verify_user
from ..handlers.customer_handler import HandleCustomersRequest
from typing import Optional
from core.data_formats.enums.dd_enums import ImportExportTypeEnum
from core.utils.export_func import create_excel_export
from models.response_models.req_res_models import SuccessResponseTypDict,BaseResponseTypDict
from core.data_formats.enums.user_enums import UserRoles
from models.import_export_models.exports.excel_headings_mapper import ACCOUNTS_MAPPER
from schemas.request_schemas.export import ExportFields
from infras.primary_db.repos.customer_repo import CustomersRepo
from tasks.arq_tasks.enqueues.report import enqueue_excel_report_job
from pydantic import EmailStr
from typing import List,Optional
from icecream import ic

router=APIRouter(
    tags=['Customer Crud'],
    prefix='/customer'
)


@router.post('')
async def add_customer(data:AddCustomerSchema,user:dict=Depends(verify_user),session:AsyncSession=Depends(get_pg_db_session)):
    return await HandleCustomersRequest(
        session=session,
        user_role=user['role'],
        cur_user_id=user['id']
    ).add(
        data=data
    )

@router.post('/bulk')
async def add_customer_bulk(user:dict=Depends(verify_user),session:AsyncSession=Depends(get_pg_db_session),type:ImportExportTypeEnum=Form(...),file:UploadFile=File(...)):
    return await HandleCustomersRequest(
        session=session,
        user_role=user['role'],
        cur_user_id=user['id']
    ).add_bulk(type=type,file=file)

@router.put('')
async def update_customer(data:UpdateCustomerSchema,user:dict=Depends(verify_user),session:AsyncSession=Depends(get_pg_db_session)):
    return await HandleCustomersRequest(
        session=session,
        user_role=user['role'],
        cur_user_id=user['id']
    ).update(
        data=data
    )


@router.delete('/{customer_id}')
async def delete_customer(customer_id:str,user:dict=Depends(verify_user),soft_delete:Optional[bool]=Query(True),session:AsyncSession=Depends(get_pg_db_session)):
    return await HandleCustomersRequest(
        session=session,
        user_role=user['role'],
        cur_user_id=user['id']
    ).delete(
        customer_id=customer_id,
        soft_delete=soft_delete
    )


@router.post('/export')
async def export(data:ExportFields,bgt:BackgroundTasks,user:dict=Depends(verify_user)):

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
        kwargs={},
        emails_tosend=[user_email],
        custom_fields=data.fields,
        mapper=ACCOUNTS_MAPPER,
        data_cls=CustomersRepo,
        data_key='customers',
        converter_name='accounts',
        sheet_name="Accounts",
        file_name='TibosCrmAccountsExport.xlsx',
        report_name="Tibos CRM Accounts Report"
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
    fields=list(ACCOUNTS_MAPPER.values())
    return SuccessResponseTypDict(
        detail=BaseResponseTypDict(
            msg="Export Fields fetched successfully",
            status_code=200,
            success=True
        ),
        data=fields
    )


@router.put('/recover')
async def recover_customer(data:RecoverCustomerSchema,user:dict=Depends(verify_user),session:AsyncSession=Depends(get_pg_db_session)):
    return await HandleCustomersRequest(
        session=session,
        user_role=user['role'],
        cur_user_id=user['id']
    ).recover(
        data=data
    )


@router.get('')
async def get_all_customer(user:dict=Depends(verify_user),q:str=Query(''),cursor:Optional[str]=Query('1'),page:Optional[str]=Query('1'),limit:Optional[int]=Query(10),session:AsyncSession=Depends(get_pg_db_session)):
    ic(cursor)
    ic(page)
    try:
        cursor=int(cursor)
    except:
        cursor=None

    try:
        page=int(page)
    except:
        page=None
    return await HandleCustomersRequest(
        session=session,
        user_role=user['role'],
        cur_user_id=user['id']
    ).get(cursor=cursor,limit=limit,query=q,page=page)


@router.get('/search',response_model=FinalResponseModel)
async def get_searched_customers(q:str=Query(...),user:dict=Depends(verify_user),session:AsyncSession=Depends(get_pg_db_session)):
    return await HandleCustomersRequest(
        session=session,
        user_role=user['role'],
        cur_user_id=user['id']
    ).search(query=q)


@router.get('/{customer_id}')
async def get_customer_by_id(customer_id:str,user:dict=Depends(verify_user),session:AsyncSession=Depends(get_pg_db_session)):
    return await HandleCustomersRequest(
        session=session,
        user_role=user['role'],
        cur_user_id=user['id']
    ).get_by_id(customer_id=customer_id)



