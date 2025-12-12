from fastapi import Depends,APIRouter,Query
from api.schemas.order import AddOrderSchema,UpdateOrderSchema
from database.configs.pg_config import get_pg_db_session,AsyncSession
from api.dependencies.token_verification import verify_user
from operations.crud.order_crud import OrdersCrud
from typing import Optional


router=APIRouter(
    tags=['Order Crud']
)


@router.post('/order')
async def add_order(data:AddOrderSchema,user:dict=Depends(verify_user),session:AsyncSession=Depends(get_pg_db_session)):
    data.delivery_info['shipping_method']=data.delivery_info['shipping_method'].value
    data.delivery_info['delivery_date']=str(data.delivery_info['delivery_date'])
    data.delivery_info['requested_date']=str(data.delivery_info['requested_date'])
    return await OrdersCrud(
        session=session,
        user_role=user['role']
    ).add(
        customer_id=data.customer_id,
        product_id=data.product_id,
        qty=data.quantity,
        total_price=data.total_price,
        discount_price=data.discount_price,
        final_price=data.final_price,
        delivery_info=data.delivery_info,
        payment_status=data.payment_status,
        invoice_status=data.invoice_status
    )


@router.put('/order')
async def update_order(data:UpdateOrderSchema,user:dict=Depends(verify_user),session:AsyncSession=Depends(get_pg_db_session)):
    data.delivery_info['shipping_method']=data.delivery_info['shipping_method'].value
    data.delivery_info['delivery_date']=str(data.delivery_info['delivery_date'])
    data.delivery_info['requested_date']=str(data.delivery_info['requested_date'])
    return await OrdersCrud(
        session=session,
        user_role=user['role']
    ).update(
        order_id=data.order_id,
        customer_id=data.customer_id,
        product_id=data.product_id,
        qty=data.quantity,
        total_price=data.total_price,
        discount_price=data.discount_price,
        final_price=data.final_price,
        delivery_info=data.delivery_info,
        payment_status=data.payment_status,
        invoice_status=data.invoice_status
    )


@router.delete('/order/{customer_id}/{order_id}')
async def delete_order(customer_id:str,order_id:str,user:dict=Depends(verify_user),session:AsyncSession=Depends(get_pg_db_session)):
    return await OrdersCrud(
        session=session,
        user_role=user['role']
    ).delete(
        customer_id=customer_id,
        order_id=order_id
    )


@router.get('/order')
async def get_all_order(q:str=Query(''),offset:Optional[int]=Query(1),limit:Optional[int]=Query(10),user:dict=Depends(verify_user),session:AsyncSession=Depends(get_pg_db_session)):
    return await OrdersCrud(
        session=session,
        user_role=user['role']
    ).get(offset=offset,limit=limit,query=q)


@router.get('/order/search')
async def get_all_order(q:str=Query(...),user:dict=Depends(verify_user),session:AsyncSession=Depends(get_pg_db_session)):
    return await OrdersCrud(
        session=session,
        user_role=user['role']
    ).search(query=q)


@router.get('/order/{order_id}')
async def get_order_by_order_id(order_id:str,user:dict=Depends(verify_user),session:AsyncSession=Depends(get_pg_db_session)):
    return await OrdersCrud(
        session=session,
        user_role=user['role']
    ).get_by_id(order_id=order_id)



@router.get('/order/customer/{customer_id}')
async def get_order_by_customer_id(customer_id:str,user:dict=Depends(verify_user),offset:Optional[int]=Query(1),limit:Optional[int]=Query(10),session:AsyncSession=Depends(get_pg_db_session)):
    return await OrdersCrud(
        session=session,
        user_role=user['role']
    ).get_by_customer_id(customer_id=customer_id,offset=offset,limit=limit)
