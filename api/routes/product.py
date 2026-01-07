from fastapi import Depends,APIRouter,Query
from schemas.request_schemas.product import AddProductSchema,UpdateProductSchema
from infras.primary_db.main import get_pg_db_session,AsyncSession
from api.dependencies.token_verification import verify_user
from ..handlers.product_handler import HandleProductsRequest
from typing import Optional


router=APIRouter(
    tags=['Product Crud'],
    prefix='/product'
)


@router.post('')
async def add_product(data:AddProductSchema,user:dict=Depends(verify_user),session:AsyncSession=Depends(get_pg_db_session)):
    return await HandleProductsRequest(
        session=session,
        user_role=user['role']
    ).add(
        data=data
    )


@router.put('')
async def update_product(data:UpdateProductSchema,user:dict=Depends(verify_user),session:AsyncSession=Depends(get_pg_db_session)):
    return await HandleProductsRequest(
        session=session,
        user_role=user['role']
    ).update(
        data=data
    )


@router.delete('/{product_id}')
async def delete_product(product_id:str,user:dict=Depends(verify_user),session:AsyncSession=Depends(get_pg_db_session)):
    return await HandleProductsRequest(
        session=session,
        user_role=user['role']
    ).delete(
        product_id=product_id
    )


@router.get('')
async def get_all_product(q:str=Query(''),offset:Optional[int]=Query(1),limit:Optional[int]=Query(10),user:dict=Depends(verify_user),session:AsyncSession=Depends(get_pg_db_session)):
    return await HandleProductsRequest(
        session=session,
        user_role=user['role']
    ).get(offset=offset,limit=limit,query=q)

@router.get('/search')
async def get_searched_product(q:str=Query(...),user:dict=Depends(verify_user),session:AsyncSession=Depends(get_pg_db_session)):
    return await HandleProductsRequest(
        session=session,
        user_role=user['role']
    ).search(query=q)

@router.get('/{product_id}')
async def get_product_by_id(product_id:str,user:dict=Depends(verify_user),session:AsyncSession=Depends(get_pg_db_session)):
    return await HandleProductsRequest(
        session=session,
        user_role=user['role']
    ).get_by_id(product_id=product_id)