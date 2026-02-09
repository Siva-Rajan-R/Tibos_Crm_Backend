from fastapi import Depends,APIRouter,Query,File,UploadFile,Form
from schemas.request_schemas.contact import AddContactSchema,UpdateContactSchema,RecoverContactSchema
from infras.primary_db.main import get_pg_db_session,AsyncSession
from api.dependencies.token_verification import verify_user
from ..handlers.contact_handler import HandleContactsRequest
from typing import Optional,Literal
from core.data_formats.enums.common_enums import ImportExportTypeEnum


router=APIRouter(
    tags=['Contact Crud'],
    prefix='/contact'
)


@router.post('')
async def add_contact(data:AddContactSchema,user:dict=Depends(verify_user),session:AsyncSession=Depends(get_pg_db_session)):
    return await HandleContactsRequest(
        session=session,
        user_role=user['role'],
        cur_user_id=user['id']
    ).add(
        data=data
    )


@router.post('/bulk')
async def add_customer_bulk(user:dict=Depends(verify_user),session:AsyncSession=Depends(get_pg_db_session),type:ImportExportTypeEnum=Form(...),file:UploadFile=File(...)):
    return await HandleContactsRequest(
        session=session,
        user_role=user['role'],
        cur_user_id=user['id']
    ).add_bulk(type=type,file=file)


@router.put('')
async def update_contact(data:UpdateContactSchema,user:dict=Depends(verify_user),session:AsyncSession=Depends(get_pg_db_session)):
    return await HandleContactsRequest(
        session=session,
        user_role=user['role'],
        cur_user_id=user['id']
    ).update(
        data=data
    )


@router.delete('/{customer_id}/{contact_id}')
async def delete_contact(customer_id:str,contact_id:str,user:dict=Depends(verify_user),soft_delete:Optional[bool]=Query(True),session:AsyncSession=Depends(get_pg_db_session)):
    return await HandleContactsRequest(
        session=session,
        user_role=user['role'],
        cur_user_id=user['id']
    ).delete(
        customer_id=customer_id,
        contact_id=contact_id,
        soft_delete=soft_delete
    )


@router.put('/recover')
async def recover_contact(data:RecoverContactSchema,user:dict=Depends(verify_user),session:AsyncSession=Depends(get_pg_db_session)):
    return await HandleContactsRequest(
        session=session,
        user_role=user['role'],
        cur_user_id=user['id']
    ).recover(
        data=data
    )



@router.get('')
async def get_all_contact(user:dict=Depends(verify_user),q:str=Query(''),cursor:Optional[int]=Query(1),limit:Optional[int]=Query(10),session:AsyncSession=Depends(get_pg_db_session)):
    return await HandleContactsRequest(
        session=session,
        user_role=user['role'],
        cur_user_id=user['id']
    ).get(cursor=cursor,limit=limit,query=q)


@router.get('/search')
async def get_all_contact(q:str=Query(...),user:dict=Depends(verify_user),session:AsyncSession=Depends(get_pg_db_session)):
    return await HandleContactsRequest(
        session=session,
        user_role=user['role'],
        cur_user_id=user['id']
    ).search(query=q)


@router.get('/{contact_id}')
async def get_contact_by_contact_id(contact_id:str,user:dict=Depends(verify_user),session:AsyncSession=Depends(get_pg_db_session)):
    return await HandleContactsRequest(
        session=session,
        user_role=user['role'],
        cur_user_id=user['id']
    ).get_by_id(contact_id=contact_id)

@router.get('/customer/{customer_id}')
async def get_contact_by_customer_id(customer_id:str,user:dict=Depends(verify_user),q:Optional[str]=Query(''),offset:Optional[int]=Query(1),limit:Optional[int]=Query(10),session:AsyncSession=Depends(get_pg_db_session)):
    return await HandleContactsRequest(
        session=session,
        user_role=user['role'],
        cur_user_id=user['id']
    ).get_by_customer_id(customer_id=customer_id,offset=offset,limit=limit,query=q)
