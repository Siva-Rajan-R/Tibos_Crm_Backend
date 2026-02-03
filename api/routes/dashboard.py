from fastapi import Depends,APIRouter,Query
from infras.primary_db.main import get_pg_db_session,AsyncSession
from api.dependencies.token_verification import verify_user
from typing import Optional
from datetime import datetime
from typing import Optional
from icecream import ic
from ..handlers.dashboard_handler import HandleDashboardRequest

router=APIRouter(
    tags=['Dashboard'],
    prefix='/dashboard'
)


@router.get('/weeks')
async def get_dashboard_totals(from_date: Optional[datetime]=Query(None),to_date:Optional[datetime]=Query(None),timezone: Optional[str] = Query("Asia/Kolkata"), session: AsyncSession = Depends(get_pg_db_session),user:dict=Depends(verify_user)):
    return await HandleDashboardRequest(session=session,user_role=user['role'],cur_user_id=user['id']).get_dashboard(from_date=from_date,to_date=to_date,timezone=timezone)
    



    
    