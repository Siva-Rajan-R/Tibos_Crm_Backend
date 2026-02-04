from fastapi import Depends, APIRouter, Query
from typing import Optional
from  infras.primary_db.main import get_pg_db_session, AsyncSession
from api.dependencies.token_verification import verify_user
from ..handlers.lead_handler import HandleLeadsRequest
from schemas.request_schemas.lead import AddLeadSchema, UpdateLeadSchema, RecoverLeadSchema

router = APIRouter(
    tags=["Leads CRUD"],
    prefix='/leads'
)


@router.post("")
async def add_lead(
    data: AddLeadSchema,
    user: dict = Depends(verify_user),
    session: AsyncSession = Depends(get_pg_db_session)
):
    return await HandleLeadsRequest(
        session=session,
        user_role=user["role"]
    ).add(
        data=data
    )


@router.put("")
async def update_lead(
    data: UpdateLeadSchema,
    user: dict = Depends(verify_user),
    session: AsyncSession = Depends(get_pg_db_session)
):
    return await HandleLeadsRequest(
        session=session,
        user_role=user["role"],
        cur_user_id=user['id']
    ).update(
        data=data
    )


@router.delete("/{lead_id}")
async def delete_lead(
    lead_id: str,
    user: dict = Depends(verify_user),
    session: AsyncSession = Depends(get_pg_db_session),
    soft_delete:Optional[bool]=Query(True)
):
    return await HandleLeadsRequest(
        session=session,
        user_role=user["role"],
        cur_user_id=user['id']
    ).delete(lead_id=lead_id,soft_delete=soft_delete)



@router.put("/recover")
async def recover_lead(
    data:RecoverLeadSchema,
    user: dict = Depends(verify_user),
    session: AsyncSession = Depends(get_pg_db_session)
):
    return await HandleLeadsRequest(
        session=session,
        user_role=user["role"],
        cur_user_id=user['id']
    ).recover(data=data)


@router.get("")
async def get_leads(
    user: dict = Depends(verify_user),
    q: str = Query(""),
    cursor: Optional[int] = Query(1),
    limit: Optional[int] = Query(10),
    session: AsyncSession = Depends(get_pg_db_session)
):
    return await HandleLeadsRequest(
        session=session,
        user_role=user["role"],
        cur_user_id=user['id']
    ).get(cursor=cursor, limit=limit, query=q)

@router.get("/search")
async def get_leads(
    user: dict = Depends(verify_user),
    q: str = Query(""),
    session: AsyncSession = Depends(get_pg_db_session)
):
    return await HandleLeadsRequest(
        session=session,
        user_role=user["role"],
        cur_user_id=user['id']
    ).search(query=q)

@router.get("/{lead_id}")
async def get_lead_by_id(
    lead_id: str,
    user: dict = Depends(verify_user),
    session: AsyncSession = Depends(get_pg_db_session)
):
    return await HandleLeadsRequest(
        session=session,
        user_role=user["role"],
        cur_user_id=user['id']
    ).get_by_id(lead_id=lead_id)
