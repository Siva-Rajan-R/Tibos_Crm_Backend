from fastapi import Depends,APIRouter,Query,File,UploadFile,Form
from schemas.request_schemas.distributor import CreateDistriSchema,UpdateDistriSchema,RecoverDistriSchema
from infras.primary_db.main import get_pg_db_session,AsyncSession
from api.dependencies.token_verification import verify_user
from ..handlers.distributor_handler import HandleDistributorRequest
from typing import Optional
from core.data_formats.enums.common_enums import ImportExportTypeEnum


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
async def add_customer_bulk(user:dict=Depends(verify_user),session:AsyncSession=Depends(get_pg_db_session),type:ImportExportTypeEnum=Form(...),file:UploadFile=File(...)):
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



