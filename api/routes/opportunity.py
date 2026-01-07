from fastapi import Depends, APIRouter,Query
from infras.primary_db.main import get_pg_db_session, AsyncSession
from api.dependencies.token_verification import verify_user
from ..handlers.opportunity_handler import HandleOpportunitiesRequest
from schemas.request_schemas.opportunity import CreateOpportunitySchema,UpdateOpportunitySchema,Optional

router = APIRouter(
    tags=["Opportunities CRUD"]
)


@router.post("/opportunities")
async def create_opportunity(
    data: CreateOpportunitySchema,
    user: dict = Depends(verify_user),
    session: AsyncSession = Depends(get_pg_db_session)
):
    return await HandleOpportunitiesRequest(
        session=session,
        user_role=user["role"]
    ).add(
        data=data
    )


@router.put("/opportunities")
async def update_opportunity(
    data: UpdateOpportunitySchema,
    user: dict = Depends(verify_user),
    session: AsyncSession = Depends(get_pg_db_session)
):
    return await HandleOpportunitiesRequest(
        session=session,
        user_role=user["role"]
    ).update(
        data=data
    )


@router.delete("/opportunities/{opportunity_id}")
async def delete_opportunity(
    opportunity_id: str,
    user: dict = Depends(verify_user),
    session: AsyncSession = Depends(get_pg_db_session)
):
    return await HandleOpportunitiesRequest(
        session=session,
        user_role=user["role"]
    ).delete(opportunity_id=opportunity_id)

@router.get("/opportunities")
async def get_leads(
    user: dict = Depends(verify_user),
    q: str = Query(""),
    offset: Optional[int] = Query(1),
    limit: Optional[int] = Query(10),
    session: AsyncSession = Depends(get_pg_db_session)
):
    return await HandleOpportunitiesRequest(
        session=session,
        user_role=user["role"]
    ).get(offset=offset, limit=limit, query=q)


@router.get("/opportunities/search")
async def get_leads(
    user: dict = Depends(verify_user),
    q: str = Query(""),
    session: AsyncSession = Depends(get_pg_db_session)
):
    return await HandleOpportunitiesRequest(
        session=session,
        user_role=user["role"]
    ).search(query=q)


@router.get("/opportunities/by-lead/{lead_id}")
async def get_opportunity_by_lead(
    lead_id: str,
    user: dict = Depends(verify_user),
    session: AsyncSession = Depends(get_pg_db_session)
):
    return await HandleOpportunitiesRequest(
        session=session,
        user_role=user["role"]
    ).get_by_lead(lead_id=lead_id)

@router.get("/opportunities/{opportunity_id}")
async def get_opportunity_byid(opportunity_id:str,session:AsyncSession=Depends(get_pg_db_session),user:dict=Depends(verify_user)):
    return await HandleOpportunitiesRequest(
        session=session,
        user_role=user["role"]
    ).get_by_id(opportunity_id=opportunity_id)
