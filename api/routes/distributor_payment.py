from sqlalchemy import select,delete,update,or_,func,String
from api.handlers.distributor_payment_handler import HandleDistributorPaymentRequest
from sqlalchemy.ext.asyncio import AsyncSession
from icecream import ic
from pydantic import EmailStr
from typing import Optional,List
from core.data_formats.enums.user_enums import UserRoles
from schemas.request_schemas.distributor_payment import AddDistributorPaymentSchema,UpdateDistributorPaymentSchema,RecoverDistributorPayment
from core.decorators.db_session_handler_dec import start_db_transaction
from math import ceil
from models.response_models.req_res_models import SuccessResponseTypDict,BaseResponseTypDict,ErrorResponseTypDict
from fastapi import APIRouter, Depends,Query
from infras.primary_db.main import get_pg_db_session
from ..dependencies.token_verification import verify_user


router=APIRouter(tags=['Distributors Payments'],prefix='/distributor-payments')


@router.post('')
async def add(data:AddDistributorPaymentSchema,user:dict=Depends(verify_user),session:AsyncSession=Depends(get_pg_db_session)):
    return await HandleDistributorPaymentRequest(session=session,user_role=user['role'],cur_user_id=['id']).add(data=data)

@router.put('')
async def update(data:UpdateDistributorPaymentSchema,user:dict=Depends(verify_user),session:AsyncSession=Depends(get_pg_db_session)):
    return await HandleDistributorPaymentRequest(session=session,user_role=user['role'],cur_user_id=['id']).update(data=data)


@router.delete('/{distributor_payment_id}')
async def delete(distributor_payment_id:int,soft_delete:bool=Query(False),user:dict=Depends(verify_user),session:AsyncSession=Depends(get_pg_db_session)):
    return await HandleDistributorPaymentRequest(session=session,user_role=user['role'],cur_user_id=['id']).delete(distri_payment_id=distributor_payment_id,soft_delete=soft_delete)

@router.put("/recover")
async def recover(data:RecoverDistributorPayment,user:dict=Depends(verify_user),session:AsyncSession=Depends(get_pg_db_session)):
    return await HandleDistributorPaymentRequest(session=session,user_role=user['role'],cur_user_id=['id']).recover(distri_payment_id=data.distributor_payment_id)
    

@router.get("")
async def get(cursor:int=Query(1),limit:int=Query(10),query:str=Query(""),include_deleted:bool=False,user:dict=Depends(verify_user),session:AsyncSession=Depends(get_pg_db_session)):
    return await HandleDistributorPaymentRequest(session=session,user_role=user['role'],cur_user_id=['id']).get(cursor=cursor,limit=limit,query=query,include_deleted=include_deleted)


@router.get('/search')
async def search(query:str,user:dict=Depends(verify_user),session:AsyncSession=Depends(get_pg_db_session)):
    return await HandleDistributorPaymentRequest(session=session,user_role=user['role'],cur_user_id=['id']).search(query=query)


@router.get('/{distributor_payment_id}')    
async def get_by_id(distributor_payment_id:int,user:dict=Depends(verify_user),session:AsyncSession=Depends(get_pg_db_session)):
    return await HandleDistributorPaymentRequest(session=session,user_role=user['role'],cur_user_id=['id']).get_by_id(distributor_payment_id=distributor_payment_id)


