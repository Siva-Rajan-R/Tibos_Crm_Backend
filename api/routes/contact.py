from fastapi import Depends,APIRouter,Query,File,UploadFile,Form,BackgroundTasks,HTTPException
from schemas.request_schemas.contact import AddContactSchema,UpdateContactSchema,RecoverContactSchema
from infras.primary_db.main import get_pg_db_session,AsyncSession
from api.dependencies.token_verification import verify_user
from ..handlers.contact_handler import HandleContactsRequest
from typing import Optional,Literal
from core.data_formats.enums.dd_enums import ImportExportTypeEnum
from models.response_models.req_res_models import SuccessResponseTypDict,BaseResponseTypDict
from core.utils.export_func import create_contact_excel_export
from core.data_formats.enums.user_enums import UserRoles


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
async def add_contact_bulk(user:dict=Depends(verify_user),session:AsyncSession=Depends(get_pg_db_session),type:ImportExportTypeEnum=Form(...),file:UploadFile=File(...)):
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


@router.get('/export')
async def export(bgt:BackgroundTasks,user:dict=Depends(verify_user)):
    if user['role']!=UserRoles.SUPER_ADMIN.value:
        raise HTTPException(
            status_code=401,
            detail="Insufficient Permission"
        )
    bgt.add_task(create_contact_excel_export,emails_tosend=[user['email']])
    return SuccessResponseTypDict(
        detail=BaseResponseTypDict(
            msg="Excel sheet generation started, It will be sended to ur email",
            status_code=200,
            success=True
        )
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
async def get_contact_by_customer_id(customer_id:str,user:dict=Depends(verify_user),cursor:Optional[int]=Query(1),limit:Optional[int]=Query(10),session:AsyncSession=Depends(get_pg_db_session)):
    return await HandleContactsRequest(
        session=session,
        user_role=user['role'],
        cur_user_id=user['id']
    ).get_by_customer_id(customer_id=customer_id,cursor=cursor,limit=limit)
