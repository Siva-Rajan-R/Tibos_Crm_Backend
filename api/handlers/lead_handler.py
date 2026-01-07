from infras.primary_db.services.lead_service import LeadsService
from sqlalchemy import select, delete, update, or_, func,String
from sqlalchemy.ext.asyncio import AsyncSession
from icecream import ic
from core.data_formats.enums.common_enums import UserRoles
from core.data_formats.enums.pg_enums import OpportunityStatus,LeadSource,LeadStatus
from math import ceil
from datetime import datetime
from typing import Optional
from schemas.db_schemas.lead import AddLeadDbSchema,UpdateLeadDbSchema
from schemas.request_schemas.lead import AddLeadSchema,UpdateLeadSchema
from core.decorators.error_handler_dec import catch_errors


class HandleLeadsRequest:
    def __init__(self, session: AsyncSession, user_role: UserRoles):
        self.session = session
        self.user_role = user_role


        if self.user_role == UserRoles.USER.value:
            return None

    @catch_errors
    async def add(self,data:AddLeadSchema):
        return await LeadsService(session=self.session,user_role=self.user_role).add(data=data)
    
    @catch_errors
    async def update(self,data:UpdateLeadSchema):
        return await LeadsService(session=self.session,user_role=self.user_role).update(data=data)

    @catch_errors
    async def delete(self, lead_id: str):
        return await LeadsService(session=self.session,user_role=self.user_role).delete(lead_id=lead_id)
    
    @catch_errors
    async def get(self, offset: int = 1, limit: int = 10, query: str = ""):
        return await LeadsService(session=self.session,user_role=self.user_role).get(offset=offset,limit=limit,query=query)

    @catch_errors
    async def get_by_id(self, lead_id: str):
        return await LeadsService(session=self.session,user_role=self.user_role).get_by_id(lead_id=lead_id)
    
    @catch_errors
    async def search(self, query: str):
        return await LeadsService(session=self.session,user_role=self.user_role).search(query=query)
