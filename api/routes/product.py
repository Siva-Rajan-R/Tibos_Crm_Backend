from fastapi import Depends,APIRouter,Query
from api.schemas.product import AddProductSchema,UpdateProductSchema
from database.configs.pg_config import get_pg_db_session,AsyncSession
from api.dependencies.token_verification import verify_user
from operations.crud.product_crud import ProductsCrud
from typing import Optional


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
async def get_all_product(q:str=Query(''),offset:Optional[int]=Query(1),limit:Optional[int]=Query(10),user:dict=Depends(verify_user),session:AsyncSession=Depends(get_pg_db_session)):
    return await ProductsCrud(
        session=session,
        user_role=user['role']
    ).get(offset=offset,limit=limit,query=q)

@router.get('/product/search')
async def get_searched_product(q:str=Query(...),user:dict=Depends(verify_user),session:AsyncSession=Depends(get_pg_db_session)):
    return await ProductsCrud(
        session=session,
        user_role=user['role']
    ).search(query=q)

@router.get('/product/{product_id}')
async def get_product_by_id(product_id:str,user:dict=Depends(verify_user),session:AsyncSession=Depends(get_pg_db_session)):
    return await ProductsCrud(
        session=session,
        user_role=user['role']
    ).get_by_id(product_id=product_id)