from fastapi import Depends,APIRouter,Query,File,UploadFile,Form
from schemas.request_schemas.customer import AddCustomerSchema,UpdateCustomerSchema,RecoverCustomerSchema
from infras.primary_db.main import get_pg_db_session,AsyncSession
from api.dependencies.token_verification import verify_user
from ..handlers.customer_handler import HandleCustomersRequest
from typing import Optional
from core.data_formats.enums.common_enums import ImportExportTypeEnum


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
async def get_all_customer(user:dict=Depends(verify_user),q:str=Query(''),offset:Optional[int]=Query(1),limit:Optional[int]=Query(10),session:AsyncSession=Depends(get_pg_db_session)):
    return await HandleCustomersRequest(
        session=session,
        user_role=user['role'],
        cur_user_id=user['id']
    ).get(offset=offset,limit=limit,query=q)


@router.get('/search')
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



