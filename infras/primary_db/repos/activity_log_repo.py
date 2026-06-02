from . import BaseRepoModel
from ..models.activity_log import ActivityLog
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from schemas.db_schemas.activity_log import CreateActivityLogDbSchema
from core.decorators.db_session_handler_dec import start_db_transaction
from core.data_formats.enums.user_enums import UserRoles

class ActivityLogRepo:
    def __init__(self, session: AsyncSession, user_role: UserRoles, cur_user_id: str):
        self.session = session
        self.user_role = user_role
        self.cur_user_id = cur_user_id

    @start_db_transaction
    async def add(self, data: CreateActivityLogDbSchema):
        self.session.add(ActivityLog(**data.model_dump(mode='json')))
        return True

    @start_db_transaction
    async def add_bulk(self, datas: List[CreateActivityLogDbSchema]):
        self.session.add_all([ActivityLog(**data.model_dump(mode='json')) for data in datas])
        return True

    async def get(self, cursor: int = 1, limit: int = 10, query: str = ""):
        from sqlalchemy import select, func, desc, String, or_, cast
        from ..models.user import Users
        from math import ceil

        offset_val = (cursor - 1) * limit if cursor > 0 else 0
        
        date_expr = func.date(func.timezone("Asia/Kolkata", ActivityLog.created_at))
        
        stmt = (
            select(
                ActivityLog.id,
                ActivityLog.action,
                ActivityLog.entity_type,
                ActivityLog.entity_id,
                ActivityLog.details,
                ActivityLog.created_at,
                Users.name.label("user_name"),
            )
            .join(Users, Users.id == ActivityLog.user_id, isouter=True)
        )
        
        if query:
            search_pattern = f"%{query}%"
            stmt = stmt.where(
                or_(
                    ActivityLog.action.ilike(search_pattern),
                    ActivityLog.entity_type.ilike(search_pattern),
                    Users.name.ilike(search_pattern),
                    cast(ActivityLog.details, String).ilike(search_pattern)
                )
            )
            
        stmt = stmt.order_by(desc(ActivityLog.created_at)).limit(limit).offset(offset_val)

        queried_logs = (await self.session.execute(stmt)).mappings().all()

        total_logs = 0
        if cursor == 1:
            count_stmt = select(func.count(ActivityLog.id)).join(Users, Users.id == ActivityLog.user_id, isouter=True)
            if query:
                search_pattern = f"%{query}%"
                count_stmt = count_stmt.where(
                    or_(
                        ActivityLog.action.ilike(search_pattern),
                        ActivityLog.entity_type.ilike(search_pattern),
                        Users.name.ilike(search_pattern),
                        cast(ActivityLog.details, String).ilike(search_pattern)
                    )
                )
            total_logs = (await self.session.execute(count_stmt)).scalar_one_or_none()

        return {
            'logs': queried_logs,
            'total_logs': total_logs,
            'total_pages': ceil(total_logs / limit) if total_logs else 0,
            'next_cursor': cursor + 1 if len(queried_logs) == limit else None
        }
