from fastapi import Depends,APIRouter,Query
from schemas.request_schemas.contact import AddContactSchema,UpdateContactSchema
from infras.primary_db.main import get_pg_db_session,AsyncSession
from api.dependencies.token_verification import verify_user
from ..handlers.contact_handler import HandleContactsRequest
from typing import Optional


router=APIRouter(
    tags=['Contact Crud']
)


@router.post('/contact')
async def add_contact(data:AddContactSchema,user:dict=Depends(verify_user),session:AsyncSession=Depends(get_pg_db_session)):
    return await HandleContactsRequest(
        session=session,
        user_role=user['role']
    ).add(
        data=data
    )


@router.put('/contact')
async def update_contact(data:UpdateContactSchema,user:dict=Depends(verify_user),session:AsyncSession=Depends(get_pg_db_session)):
    return await HandleContactsRequest(
        session=session,
        user_role=user['role']
    ).update(
        data=data
    )


@router.delete('/contact/{customer_id}/{contact_id}')
async def delete_contact(customer_id:str,contact_id:str,user:dict=Depends(verify_user),session:AsyncSession=Depends(get_pg_db_session)):
    return await HandleContactsRequest(
        session=session,
        user_role=user['role']
    ).delete(
        customer_id=customer_id,
        contact_id=contact_id
    )


@router.get('/contact')
async def get_all_contact(user:dict=Depends(verify_user),q:str=Query(''),offset:Optional[int]=Query(1),limit:Optional[int]=Query(10),session:AsyncSession=Depends(get_pg_db_session)):
    return await HandleContactsRequest(
        session=session,
        user_role=user['role']
    ).get(offset=offset,limit=limit,query=q)


@router.get('/contact/search')
async def get_all_contact(q:str=Query(...),user:dict=Depends(verify_user),session:AsyncSession=Depends(get_pg_db_session)):
    return await HandleContactsRequest(
        session=session,
        user_role=user['role']
    ).search(query=q)


@router.get('/contact/{contact_id}')
async def get_contact_by_contact_id(contact_id:str,user:dict=Depends(verify_user),session:AsyncSession=Depends(get_pg_db_session)):
    return await HandleContactsRequest(
        session=session,
        user_role=user['role']
    ).get_by_id(contact_id=contact_id)

@router.get('/contact/customer/{customer_id}')
async def get_contact_by_customer_id(customer_id:str,user:dict=Depends(verify_user),q:Optional[str]=Query(''),offset:Optional[int]=Query(1),limit:Optional[int]=Query(10),session:AsyncSession=Depends(get_pg_db_session)):
    return await HandleContactsRequest(
        session=session,
        user_role=user['role']
    ).get_by_customer_id(customer_id=customer_id,offset=offset,limit=limit,query=q)
