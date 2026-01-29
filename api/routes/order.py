from fastapi import Depends,APIRouter,Query
from schemas.request_schemas.order import AddOrderSchema,UpdateOrderSchema,RecoverOrderSchema
from core.data_formats.enums.filters_enum import OrdersFilters
from infras.primary_db.main import get_pg_db_session,AsyncSession
from api.dependencies.token_verification import verify_user
from ..handlers.order_handler import HandleOrdersRequest
from typing import Optional



router=APIRouter(
    tags=['Order Crud'],
    prefix='/order'
)


@router.post('')
async def add_order(data:AddOrderSchema,user:dict=Depends(verify_user),session:AsyncSession=Depends(get_pg_db_session)):
    data.delivery_info['shipping_method']=data.delivery_info['shipping_method'].value
    data.delivery_info['delivery_date']=str(data.delivery_info['delivery_date'])
    data.delivery_info['requested_date']=str(data.delivery_info['requested_date'])
    return await HandleOrdersRequest(
        session=session,
        user_role=user['role'],
        cur_user_id=user['id']
    ).add(
        data=data
    )


@router.put('')
async def update_order(data:UpdateOrderSchema,user:dict=Depends(verify_user),session:AsyncSession=Depends(get_pg_db_session)):
    return await HandleOrdersRequest(
        session=session,
        user_role=user['role'],
        cur_user_id=user['id']
    ).update(
        data=data
    )


@router.delete('/{customer_id}/{order_id}')
async def delete_order(customer_id:str,order_id:str,user:dict=Depends(verify_user),soft_delete:Optional[bool]=Query(True),session:AsyncSession=Depends(get_pg_db_session)):
    return await HandleOrdersRequest(
        session=session,
        user_role=user['role'],
        cur_user_id=user['id']
    ).delete(
        customer_id=customer_id,
        order_id=order_id,
        soft_delete=soft_delete
    )




@router.put('/recover')
async def recover_order(data:RecoverOrderSchema,user:dict=Depends(verify_user),session:AsyncSession=Depends(get_pg_db_session)):
    return await HandleOrdersRequest(
        session=session,
        user_role=user['role'],
        cur_user_id=user['id']
    ).recover(
        data=data
    )


@router.get('')
async def get_all_order(q:str=Query(''),offset:Optional[int]=Query(1),limit:Optional[int]=Query(10),filter:Optional[OrdersFilters]=Query(None),user:dict=Depends(verify_user),session:AsyncSession=Depends(get_pg_db_session)):
    return await HandleOrdersRequest(
        session=session,
        user_role=user['role'],
        cur_user_id=user['id']
    ).get(offset=offset,limit=limit,query=q,filter=filter)


@router.get('/search')
async def get_all_order(q:str=Query(...),user:dict=Depends(verify_user),session:AsyncSession=Depends(get_pg_db_session)):
    return await HandleOrdersRequest(
        session=session,
        user_role=user['role'],
        cur_user_id=user['id']
    ).search(query=q)


@router.get('/{order_id}')
async def get_order_by_order_id(order_id:str,user:dict=Depends(verify_user),session:AsyncSession=Depends(get_pg_db_session)):
    return await HandleOrdersRequest(
        session=session,
        user_role=user['role'],
        cur_user_id=user['id']
    ).get_by_id(order_id=order_id)



@router.get('/customer/{customer_id}')
async def get_order_by_customer_id(customer_id:str,user:dict=Depends(verify_user),offset:Optional[int]=Query(1),limit:Optional[int]=Query(10),session:AsyncSession=Depends(get_pg_db_session)):
    return await HandleOrdersRequest(
        session=session,
        user_role=user['role'],
        cur_user_id=user['id']
    ).get_by_customer_id(customer_id=customer_id,offset=offset,limit=limit)
