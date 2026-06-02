from fastapi import APIRouter, Depends, Query
from infras.primary_db.main import get_pg_db_session
from api.dependencies.token_verification import verify_user
from ..handlers.activity_log_handler import ActivityLogHandler

router = APIRouter(
    tags=['Activity Logs'],
    prefix='/activity-logs'
)

from typing import Optional

@router.get('')
async def get_activity_logs(cursor: int = Query(1), limit: int = Query(10), query: str = Query(""), from_date: Optional[str] = Query(None), to_date: Optional[str] = Query(None), user: dict = Depends(verify_user), session = Depends(get_pg_db_session)):
    return await ActivityLogHandler(session=session, user_role=user['role'], cur_user_id=user['id']).get(cursor=cursor, limit=limit, query=query, from_date=from_date, to_date=to_date)
