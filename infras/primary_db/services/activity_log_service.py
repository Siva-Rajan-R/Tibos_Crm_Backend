from . import BaseServiceModel
from ..repos.activity_log_repo import ActivityLogRepo
from schemas.db_schemas.activity_log import CreateActivityLogDbSchema
from core.decorators.error_handler_dec import catch_errors
from sqlalchemy.ext.asyncio import AsyncSession
from core.data_formats.enums.user_enums import UserRoles
from typing import List, Dict, Any, Optional
from core.utils.uuid_generator import generate_uuid

class ActivityLogService:
    def __init__(self, session: AsyncSession, user_role: UserRoles, cur_user_id: str):
        self.session = session
        self.user_role = user_role
        self.cur_user_id = cur_user_id

    @catch_errors
    async def log_action(self, action: str, entity_type: str, entity_id: str, details: Optional[Dict[str, Any]] = None):
        log_id: str = generate_uuid()
        repo = ActivityLogRepo(session=self.session, user_role=self.user_role, cur_user_id=self.cur_user_id)
        data = CreateActivityLogDbSchema(
            id=log_id,
            user_id=self.cur_user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            details=details
        )
        return await repo.add(data=data)

    @catch_errors
    async def log_bulk_actions(self, action: str, entity_type: str, entity_ids: List[str], details: Optional[Dict[str, Any]] = None):
        repo = ActivityLogRepo(session=self.session, user_role=self.user_role, cur_user_id=self.cur_user_id)
        datas = []
        for entity_id in entity_ids:
            log_id: str = generate_uuid()
            datas.append(CreateActivityLogDbSchema(
                id=log_id,
                user_id=self.cur_user_id,
                action=action,
                entity_type=entity_type,
                entity_id=entity_id,
                details=details
            ))
        if datas:
            return await repo.add_bulk(datas=datas)
        return True

    @catch_errors
    async def get(self, cursor: int = 1, limit: int = 10, query: str = "", from_date: Optional[str] = None, to_date: Optional[str] = None):
        repo = ActivityLogRepo(session=self.session, user_role=self.user_role, cur_user_id=self.cur_user_id)
        return await repo.get(cursor=cursor, limit=limit, query=query, from_date=from_date, to_date=to_date)
