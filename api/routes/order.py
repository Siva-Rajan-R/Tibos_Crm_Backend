from fastapi import Depends,APIRouter
from api.schemas.order import AddOrderSchema,UpdateOrderSchema
from database.configs.pg_config import get_pg_db_session,AsyncSession
from api.dependencies.token_verification import verify_user
from crud.order_crud import OrdersCrud


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
        delivery_info=data.delivery_info
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
        delivery_info=data.delivery_info
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
async def get_all_order(user:dict=Depends(verify_user),session:AsyncSession=Depends(get_pg_db_session)):
    return await OrdersCrud(
        session=session,
        user_role=user['role']
    ).get()


@router.get('/order/{order_id}')
async def get_order_by_order_id(order_id:str,user:dict=Depends(verify_user),session:AsyncSession=Depends(get_pg_db_session)):
    return await OrdersCrud(
        session=session,
        user_role=user['role']
    ).get_by_order_id(order_id=order_id)

@router.get('/order/customer/{customer_id}')
async def get_order_by_customer_id(customer_id:str,user:dict=Depends(verify_user),session:AsyncSession=Depends(get_pg_db_session)):
    return await OrdersCrud(
        session=session,
        user_role=user['role']
    ).get_by_customer_id(customer_id=customer_id)