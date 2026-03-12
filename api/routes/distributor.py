from fastapi import Depends,APIRouter,Query,File,UploadFile,Form,BackgroundTasks,HTTPException
from schemas.request_schemas.distributor import CreateDistriSchema,UpdateDistriSchema,RecoverDistriSchema
from infras.primary_db.main import get_pg_db_session,AsyncSession
from api.dependencies.token_verification import verify_user
from ..handlers.distributor_handler import HandleDistributorRequest
from typing import Optional
from core.data_formats.enums.dd_enums import ImportExportTypeEnum
from models.response_models.req_res_models import SuccessResponseTypDict,BaseResponseTypDict
from core.utils.export_func import create_excel_export
from infras.primary_db.repos.distri_repo import DistributorsRepo
from core.data_formats.enums.user_enums import UserRoles
from models.import_export_models.exports.excel_headings_mapper import DISTRI_MAPPER
from schemas.request_schemas.export import ExportFields
from tasks.arq_tasks.enqueues.report import enqueue_excel_report_job
from pydantic import EmailStr


router=APIRouter(
    tags=['Distributor Crud'],
    prefix='/distributor'
)


@router.post('')
async def add_distributor(data:CreateDistriSchema,user:dict=Depends(verify_user),session:AsyncSession=Depends(get_pg_db_session)):
    return await HandleDistributorRequest(
        session=session,
        user_role=user['role'],
        cur_user_id=user['id']
    ).add(
        data=data
    )

@router.post('/bulk')
async def add_distributor_bulk(user:dict=Depends(verify_user),session:AsyncSession=Depends(get_pg_db_session),type:ImportExportTypeEnum=Form(...),file:UploadFile=File(...)):
    return await HandleDistributorRequest(
        session=session,
        user_role=user['role'],
        cur_user_id=user['id']
    ).add_bulk(type=type,file=file)


@router.put('')
async def update_distributor(data:UpdateDistriSchema,user:dict=Depends(verify_user),session:AsyncSession=Depends(get_pg_db_session)):
    return await HandleDistributorRequest(
        session=session,
        user_role=user['role'],
        cur_user_id=user['id']
    ).update(
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
        emails_tosend=[user_email],
        kwargs={},
        custom_fields=data.fields,
        mapper=DISTRI_MAPPER,
        data_cls=DistributorsRepo,
        data_key='distributors',
        converter_name='distributors',
        sheet_name="Distributors",
        file_name='TibosCrmDistributorsExport.xlsx',
        report_name="Tibos CRM Distributors Report"
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
    fields=list(DISTRI_MAPPER.values())
    return SuccessResponseTypDict(
        detail=BaseResponseTypDict(
            msg="Export Fields fetched successfully",
            status_code=200,
            success=True
        ),
        data=fields
    )


@router.delete('/{distributor_id}')
async def delete_distributor(distributor_id:str,user:dict=Depends(verify_user),soft_delete:Optional[bool]=Query(True),session:AsyncSession=Depends(get_pg_db_session)):
    return await HandleDistributorRequest(
        session=session,
        user_role=user['role'],
        cur_user_id=user['id']
    ).delete(
        distributor_id=distributor_id,
        soft_delete=soft_delete
    )


@router.put('/recover')
async def recover_distributor(data:RecoverDistriSchema,user:dict=Depends(verify_user),session:AsyncSession=Depends(get_pg_db_session)):
    return await HandleDistributorRequest(
        session=session,
        user_role=user['role'],
        cur_user_id=user['id']
    ).recover(
        data=data
    )


@router.get('')
async def get_all_distributor(user:dict=Depends(verify_user),q:str=Query(''),cursor:Optional[int]=Query(1),limit:Optional[int]=Query(10),session:AsyncSession=Depends(get_pg_db_session)):
    return await HandleDistributorRequest(
        session=session,
        user_role=user['role'],
        cur_user_id=user['id']
    ).get(cursor=cursor,limit=limit,query=q)


@router.get('/search')
async def get_searched_distributors(q:str=Query(...),user:dict=Depends(verify_user),session:AsyncSession=Depends(get_pg_db_session)):
    return await HandleDistributorRequest(
        session=session,
        user_role=user['role'],
        cur_user_id=user['id']
    ).search(query=q)


@router.get('/{distributor_id}')
async def get_distributor_by_id(distributor_id:str,user:dict=Depends(verify_user),session:AsyncSession=Depends(get_pg_db_session)):
    return await HandleDistributorRequest(
        session=session,
        user_role=user['role'],
        cur_user_id=user['id']
    ).get_by_id(distributor_id=distributor_id)



