from fastapi import Depends,APIRouter,Query
from api.schemas.customer import AddCustomerSchema,UpdateCustomerSchema
from database.configs.pg_config import get_pg_db_session,AsyncSession
from api.dependencies.token_verification import verify_user
from operations.crud.customer_crud import CustomersCrud
from typing import Optional


router=APIRouter(
    tags=['Customer Crud']
)


@router.post('/customer')
async def add_customer(data:AddCustomerSchema,user:dict=Depends(verify_user),session:AsyncSession=Depends(get_pg_db_session)):
    return await CustomersCrud(
        session=session,
        user_role=user['role']
    ).add(
        name=data.name,
        mobile_no=data.mobile_number,
        email=data.email,
        web_url=data.website_url,
        no_of_emply=data.no_of_employee,
        gst_no=data.gst_number,
        industry=data.industry,
        sector=data.sector,
        address=data.address
    )


@router.put('/customer')
async def update_customer(data:UpdateCustomerSchema,user:dict=Depends(verify_user),session:AsyncSession=Depends(get_pg_db_session)):
    return await CustomersCrud(
        session=session,
        user_role=user['role']
    ).update(
        customer_id=data.customer_id,
        name=data.name,
        mobile_no=data.mobile_number,
        email=data.email,
        web_url=data.website_url,
        no_of_emply=data.no_of_employee,
        gst_no=data.gst_number,
        industry=data.industry,
        sector=data.sector,
        address=data.address
    )


@router.delete('/customer/{customer_id}')
async def delete_customer(customer_id:str,user:dict=Depends(verify_user),session:AsyncSession=Depends(get_pg_db_session)):
    return await CustomersCrud(
        session=session,
        user_role=user['role']
    ).delete(
        customer_id=customer_id
    )


@router.get('/customer')
async def get_all_customer(user:dict=Depends(verify_user),offset:Optional[int]=Query(0),limit:Optional[int]=Query(10),session:AsyncSession=Depends(get_pg_db_session)):
    return await CustomersCrud(
        session=session,
        user_role=user['role']
    ).get(offset=offset,limit=limit)


@router.get('/customer/search')
async def get_searched_customers(q:str=Query(...),user:dict=Depends(verify_user),session:AsyncSession=Depends(get_pg_db_session)):
    return await CustomersCrud(
        session=session,
        user_role=user['role']
    ).search(query=q)


@router.get('/customer/{customer_id}')
async def get_customer_by_id(customer_id:str,user:dict=Depends(verify_user),session:AsyncSession=Depends(get_pg_db_session)):
    return await CustomersCrud(
        session=session,
        user_role=user['role']
    ).get_by_id(customer_id=customer_id)



