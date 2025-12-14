from fastapi import Depends, APIRouter, Query
from typing import Optional
from database.configs.pg_config import get_pg_db_session, AsyncSession
from api.dependencies.token_verification import verify_user
from operations.crud.lead_crud import LeadsCrud
from api.schemas.lead import AddLeadSchema, UpdateLeadSchema

router = APIRouter(
    tags=["Leads CRUD"]
)


@router.post("/leads")
async def add_lead(
    data: AddLeadSchema,
    user: dict = Depends(verify_user),
    session: AsyncSession = Depends(get_pg_db_session)
):
    return await LeadsCrud(
        session=session,
        user_role=user["role"]
    ).add(
        name=data.name,
        email=data.email,
        phone=data.phone,
        source=data.source,
        assigned_to=data.assigned_to,
        description=data.description,
        status=data.status,
        next_followup=data.next_followup,
        last_contacted=data.last_contacted
    )


@router.put("/leads")
async def update_lead(
    data: UpdateLeadSchema,
    user: dict = Depends(verify_user),
    session: AsyncSession = Depends(get_pg_db_session)
):
    return await LeadsCrud(
        session=session,
        user_role=user["role"]
    ).update(
        lead_id=data.lead_id,
        name=data.name,
        email=data.email,
        phone=data.phone,
        source=data.source,
        status=data.status,
        assigned_to=data.assigned_to,
        last_contacted=data.last_contacted,
        next_followup=data.next_followup,
        description=data.description
    )


@router.delete("/leads/{lead_id}")
async def delete_lead(
    lead_id: str,
    user: dict = Depends(verify_user),
    session: AsyncSession = Depends(get_pg_db_session)
):
    return await LeadsCrud(
        session=session,
        user_role=user["role"]
    ).delete(lead_id=lead_id)


@router.get("/leads")
async def get_leads(
    user: dict = Depends(verify_user),
    q: str = Query(""),
    offset: Optional[int] = Query(1),
    limit: Optional[int] = Query(10),
    session: AsyncSession = Depends(get_pg_db_session)
):
    return await LeadsCrud(
        session=session,
        user_role=user["role"]
    ).get(offset=offset, limit=limit, query=q)

@router.get("/leads/search")
async def get_leads(
    user: dict = Depends(verify_user),
    q: str = Query(""),
    session: AsyncSession = Depends(get_pg_db_session)
):
    return await LeadsCrud(
        session=session,
        user_role=user["role"]
    ).search(query=q)

@router.get("/leads/{lead_id}")
async def get_lead_by_id(
    lead_id: str,
    user: dict = Depends(verify_user),
    session: AsyncSession = Depends(get_pg_db_session)
):
    return await LeadsCrud(
        session=session,
        user_role=user["role"]
    ).get_by_id(lead_id=lead_id)
