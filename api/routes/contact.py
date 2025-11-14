from fastapi import Depends,APIRouter
from api.schemas.contact import AddContactSchema,UpdateContactSchema
from database.configs.pg_config import get_pg_db_session,AsyncSession
from api.dependencies.token_verification import verify_user
from operations.crud.contact_crud import ContactsCrud


router=APIRouter(
    tags=['Contact Crud']
)


@router.post('/contact')
async def add_contact(data:AddContactSchema,user:dict=Depends(verify_user),session:AsyncSession=Depends(get_pg_db_session)):
    return await ContactsCrud(
        session=session,
        user_role=user['role']
    ).add(
        name=data.name,
        customer_id=data.customer_id,
        mobile_no=data.mobile_number,
        email=data.email
    )


@router.put('/contact')
async def update_contact(data:UpdateContactSchema,user:dict=Depends(verify_user),session:AsyncSession=Depends(get_pg_db_session)):
    return await ContactsCrud(
        session=session,
        user_role=user['role']
    ).update(
        contact_id=data.contact_id,
        name=data.name,
        customer_id=data.customer_id,
        mobile_no=data.mobile_number,
        email=data.email
    )


@router.delete('/contact/{customer_id}/{contact_id}')
async def delete_contact(customer_id:str,contact_id:str,user:dict=Depends(verify_user),session:AsyncSession=Depends(get_pg_db_session)):
    return await ContactsCrud(
        session=session,
        user_role=user['role']
    ).delete(
        customer_id=customer_id,
        contact_id=contact_id
    )


@router.get('/contact')
async def get_all_contact(user:dict=Depends(verify_user),session:AsyncSession=Depends(get_pg_db_session)):
    return await ContactsCrud(
        session=session,
        user_role=user['role']
    ).get()


@router.get('/contact/{contact_id}')
async def get_contact_by_contact_id(contact_id:str,user:dict=Depends(verify_user),session:AsyncSession=Depends(get_pg_db_session)):
    return await ContactsCrud(
        session=session,
        user_role=user['role']
    ).get_by_id(contact_id=contact_id)

@router.get('/contact/customer/{customer_id}')
async def get_contact_by_customer_id(customer_id:str,user:dict=Depends(verify_user),session:AsyncSession=Depends(get_pg_db_session)):
    return await ContactsCrud(
        session=session,
        user_role=user['role']
    ).get_by_customer_id(customer_id=customer_id)