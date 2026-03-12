from fastapi import Depends,APIRouter,Query,File,UploadFile,Form,BackgroundTasks,HTTPException
from schemas.request_schemas.product import AddProductSchema,UpdateProductSchema,RecoverProductSchema
from infras.primary_db.main import get_pg_db_session,AsyncSession
from api.dependencies.token_verification import verify_user
from ..handlers.product_handler import HandleProductsRequest
from typing import Optional,Literal
from core.data_formats.enums.dd_enums import ImportExportTypeEnum
from models.response_models.req_res_models import SuccessResponseTypDict,BaseResponseTypDict
from core.utils.export_func import create_excel_export
from core.data_formats.enums.user_enums import UserRoles
from models.import_export_models.exports.excel_headings_mapper import PRODUCTS_MAPPER
from schemas.request_schemas.export import ExportFields
from infras.primary_db.repos.product_repo import ProductsRepo
from tasks.arq_tasks.enqueues.report import enqueue_excel_report_job
from pydantic import EmailStr

router=APIRouter(
    tags=['Product Crud'],
    prefix='/product'
)


@router.post('')
async def add_product(data:AddProductSchema,user:dict=Depends(verify_user),session:AsyncSession=Depends(get_pg_db_session)):
    return await HandleProductsRequest(
        session=session,
        user_role=user['role'],
        cur_user_id=user['id']
    ).add(
        data=data
    )

@router.post("/bulk")
async def add_product_bulk(type: ImportExportTypeEnum = Form(...),file: UploadFile = File(...),user:dict=Depends(verify_user),session:AsyncSession=Depends(get_pg_db_session)):
    return await HandleProductsRequest(
        session=session,
        user_role=user['role'],
        cur_user_id=user['id']
    ).add_bulk(
        type=type,
        file=file
    )


@router.put('')
async def update_product(data:UpdateProductSchema,user:dict=Depends(verify_user),session:AsyncSession=Depends(get_pg_db_session)):
    return await HandleProductsRequest(
        session=session,
        user_role=user['role'],
        cur_user_id=user['id']
    ).update(
        data=data
    )


@router.delete('/{product_id}')
async def delete_product(product_id:str,user:dict=Depends(verify_user),soft_delete:Optional[bool]=Query(True),session:AsyncSession=Depends(get_pg_db_session)):
    return await HandleProductsRequest(
        session=session,
        user_role=user['role'],
        cur_user_id=user['id']
    ).delete(
        product_id=product_id,
        soft_delete=soft_delete
    )


@router.put('/recover')
async def recover_product(data:RecoverProductSchema,user:dict=Depends(verify_user),session:AsyncSession=Depends(get_pg_db_session)):
    return await HandleProductsRequest(
        session=session,
        user_role=user['role'],
        cur_user_id=user['id']
    ).recover(
        data=data
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
        mapper=PRODUCTS_MAPPER,
        data_cls=ProductsRepo,
        data_key='products',
        converter_name='products',
        sheet_name="Products",
        file_name='TibosCrmProductsExport.xlsx',
        report_name="Tibos CRM Products Report"
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
    fields=list(PRODUCTS_MAPPER.values())
    return SuccessResponseTypDict(
        detail=BaseResponseTypDict(
            msg="Export Fields fetched successfully",
            status_code=200,
            success=True
        ),
        data=fields
    )

@router.get('')
async def get_all_product(q:str=Query(''),cursor:Optional[int]=Query(1),limit:Optional[int]=Query(10),user:dict=Depends(verify_user),session:AsyncSession=Depends(get_pg_db_session)):
    return await HandleProductsRequest(
        session=session,
        user_role=user['role'],
        cur_user_id=user['id']
    ).get(cursor=cursor,limit=limit,query=q)

@router.get('/search')
async def get_searched_product(q:str=Query(...),user:dict=Depends(verify_user),session:AsyncSession=Depends(get_pg_db_session)):
    return await HandleProductsRequest(
        session=session,
        user_role=user['role'],
        cur_user_id=user['id']
    ).search(query=q)

@router.get('/{product_id}')
async def get_product_by_id(product_id:str,user:dict=Depends(verify_user),session:AsyncSession=Depends(get_pg_db_session)):
    return await HandleProductsRequest(
        session=session,
        user_role=user['role'],
        cur_user_id=user['id']
    ).get_by_id(product_id=product_id)