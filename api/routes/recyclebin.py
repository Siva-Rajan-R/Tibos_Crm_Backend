from fastapi import APIRouter,Depends
from infras.primary_db.main import get_pg_db_session,AsyncSession
from typing import Annotated
from api.dependencies.token_verification import verify_user
from ..handlers.recyclebin_handler import HandleRecycleBinRequests


router=APIRouter(
    prefix='/recyclebin',
    tags=['Recycle Bin Service']
)

ASYNC_PG_SESSION=Annotated[AsyncSession,Depends(get_pg_db_session)]
@router.get('/')
async def get_recyclebin(session:ASYNC_PG_SESSION):
    return await HandleRecycleBinRequests(session=session).get()