from fastapi import Depends,APIRouter
from api.schemas.customer import AddCustomerSchema,UpdateCustomerSchema
from database.configs.pg_config import get_pg_db_session,AsyncSession
from api.dependencies.token_verification import verify_user
from crud.customer_crud import CustomersCrud


router=APIRouter(
    tags=['Customer Crud']
)


@router.post('/customer')
async def add_customer(data:AddCustomerSchema,user:dict=Depends(verify_user),session:AsyncSession=Depends(get_pg_db_session)):
    return await CustomersCrud(
        session=session,
        user_email=user['id'],
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
        primary_contact=data.primary_contact,
        address=data.address
    )


@router.put('/customer')
async def update_customer(data:UpdateCustomerSchema,user:dict=Depends(verify_user),session:AsyncSession=Depends(get_pg_db_session)):
    return await CustomersCrud(
        session=session,
        user_email=user['id'],
        user_role=user['role']
    ).update(
        customer_id=data.customer_id,
        name=data.name,
        mobile_no=data.mobile_number,
        email=data.email,
        web_url=data.website_url,
        no_of_emply=data.no_of_employee,
        gst_no=data.no_of_employee,
        industry=data.industry,
        sector=data.sector,
        primary_contact=data.primary_contact,
        address=data.address
    )


@router.delete('/customer/{customer_id}')
async def delete_customer(customer_id:str,user:dict=Depends(verify_user),session:AsyncSession=Depends(get_pg_db_session)):
    return await CustomersCrud(
        session=session,
        user_email=user['id'],
        user_role=user['role']
    ).delete(
        customer_id=customer_id
    )


@router.get('/customer')
async def get_all_customer(user:dict=Depends(verify_user),session:AsyncSession=Depends(get_pg_db_session)):
    return await CustomersCrud(
        session=session,
        user_email=user['id'],
        user_role=user['role']
    ).get()


@router.get('/customer/{customer_id}')
async def get_customer_by_id(customer_id:str,user:dict=Depends(verify_user),session:AsyncSession=Depends(get_pg_db_session)):
    return await CustomersCrud(
        session=session,
        user_email=user['id'],
        user_role=user['role']
    ).get_by_id(customer_id=customer_id)