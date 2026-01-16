from fastapi import Depends,APIRouter,Query
from schemas.request_schemas.distributor import CreateDistriSchema,UpdateDistriSchema
from infras.primary_db.main import get_pg_db_session,AsyncSession
from api.dependencies.token_verification import verify_user
from ..handlers.distributor_handler import HandleDistributorRequest
from typing import Optional


router=APIRouter(
    tags=['Distributor Crud'],
    prefix='/distributor'
)


@router.post('')
async def add_distributor(data:CreateDistriSchema,user:dict=Depends(verify_user),session:AsyncSession=Depends(get_pg_db_session)):
    return await HandleDistributorRequest(
        session=session,
        user_role=user['role']
    ).add(
        data=data
    )


@router.put('')
async def update_distributor(data:UpdateDistriSchema,user:dict=Depends(verify_user),session:AsyncSession=Depends(get_pg_db_session)):
    return await HandleDistributorRequest(
        session=session,
        user_role=user['role']
    ).update(
        data=data
    )


@router.delete('/{distributor_id}')
async def delete_distributor(distributor_id:str,user:dict=Depends(verify_user),session:AsyncSession=Depends(get_pg_db_session)):
    return await HandleDistributorRequest(
        session=session,
        user_role=user['role']
    ).delete(
        distributor_id=distributor_id
    )


@router.get('')
async def get_all_distributor(user:dict=Depends(verify_user),q:str=Query(''),offset:Optional[int]=Query(1),limit:Optional[int]=Query(10),session:AsyncSession=Depends(get_pg_db_session)):
    return await HandleDistributorRequest(
        session=session,
        user_role=user['role']
    ).get(offset=offset,limit=limit,query=q)


@router.get('/search')
async def get_searched_distributors(q:str=Query(...),user:dict=Depends(verify_user),session:AsyncSession=Depends(get_pg_db_session)):
    return await HandleDistributorRequest(
        session=session,
        user_role=user['role']
    ).search(query=q)


@router.get('/{distributor_id}')
async def get_distributor_by_id(distributor_id:str,user:dict=Depends(verify_user),session:AsyncSession=Depends(get_pg_db_session)):
    return await HandleDistributorRequest(
        session=session,
        user_role=user['role']
    ).get_by_id(distributor_id=distributor_id)



