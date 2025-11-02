from fastapi import Depends,APIRouter
from api.schemas.product import AddProductSchema,UpdateProductSchema
from database.configs.pg_config import get_pg_db_session,AsyncSession
from api.dependencies.token_verification import verify_user
from crud.product_crud import ProductsCrud


router=APIRouter(
    tags=['Product Crud']
)


@router.post('/product')
async def add_product(data:AddProductSchema,user:dict=Depends(verify_user),session:AsyncSession=Depends(get_pg_db_session)):
    return await ProductsCrud(
        session=session,
        user_role=user['role']
    ).add(
        name=data.name,
        description=data.description,
        price=data.price,
        ava_qty=data.available_qty,
        product_type=data.product_type
    )


@router.put('/product')
async def update_product(data:UpdateProductSchema,user:dict=Depends(verify_user),session:AsyncSession=Depends(get_pg_db_session)):
    return await ProductsCrud(
        session=session,
        user_role=user['role']
    ).update(
        product_id=data.product_id,
        name=data.name,
        description=data.description,
        price=data.price,
        ava_qty=data.available_qty,
        product_type=data.product_type
    )


@router.delete('/product/{product_id}')
async def delete_product(product_id:str,user:dict=Depends(verify_user),session:AsyncSession=Depends(get_pg_db_session)):
    return await ProductsCrud(
        session=session,
        user_role=user['role']
    ).delete(
        product_id=product_id
    )


@router.get('/product')
async def get_all_product(user:dict=Depends(verify_user),session:AsyncSession=Depends(get_pg_db_session)):
    return await ProductsCrud(
        session=session,
        user_role=user['role']
    ).get()


@router.get('/product/{product_id}')
async def get_product_by_id(product_id:str,user:dict=Depends(verify_user),session:AsyncSession=Depends(get_pg_db_session)):
    return await ProductsCrud(
        session=session,
        user_role=user['role']
    ).get_by_id(product_id=product_id)