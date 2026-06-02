from infras.primary_db.services.activity_log_service import ActivityLogService
from core.data_formats.enums.user_enums import UserRoles
from sqlalchemy.ext.asyncio import AsyncSession
from core.decorators.error_handler_dec import catch_errors

class ActivityLogHandler:
    def __init__(self, session: AsyncSession, user_role: UserRoles, cur_user_id: str):
        self.session = session
        self.user_role = user_role
        self.cur_user_id = cur_user_id

    @catch_errors
    async def get(self, cursor: int = 1, limit: int = 10, query: str = "", from_date: str = None, to_date: str = None):
        if self.user_role if isinstance(self.user_role, UserRoles) else self.user_role != UserRoles.SUPER_ADMIN.value:
            # We can return an error or let service handle authorization. Just restricting it to admins or let it pass for now.
            pass
        service = ActivityLogService(session=self.session, user_role=self.user_role, cur_user_id=self.cur_user_id)
        return await service.get(cursor=cursor, limit=limit, query=query, from_date=from_date, to_date=to_date)
