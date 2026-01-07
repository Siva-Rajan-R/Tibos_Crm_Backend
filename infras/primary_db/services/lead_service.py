from . import BaseServiceModel
from ..models.leads import Leads
from core.utils.uuid_generator import generate_uuid
from ..repos.lead_repo import LeadsRepo
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


class LeadsService(BaseServiceModel):
    def __init__(self, session: AsyncSession, user_role: UserRoles):
        self.session = session
        self.user_role = user_role


    @catch_errors
    async def add(self,data:AddLeadSchema):
        lead_id:str=generate_uuid()
        return await LeadsRepo(session=self.session,user_role=self.user_role).add(data=AddLeadDbSchema(**data.model_dump(),id=lead_id))
    
    @catch_errors
    async def update(self,data:UpdateLeadSchema):
        data_toupdate=data.model_dump(exclude_none=True,exclude_unset=True)
        if not data_toupdate or len(data_toupdate)<1:
            return False
        
        return await LeadsRepo(session=self.session,user_role=self.user_role).update(data=UpdateLeadDbSchema(**data_toupdate))

    @catch_errors
    async def delete(self, lead_id: str):
        return await LeadsRepo(session=self.session,user_role=self.user_role).delete(lead_id=lead_id)
    
    @catch_errors
    async def get(self, offset: int = 1, limit: int = 10, query: str = ""):
        return await LeadsRepo(session=self.session,user_role=self.user_role).get(offset=offset,limit=limit,query=query)

    @catch_errors
    async def get_by_id(self, lead_id: str):
        return await LeadsRepo(session=self.session,user_role=self.user_role).get_by_id(lead_id=lead_id)
    
    @catch_errors
    async def search(self, query: str):
        return await LeadsRepo(session=self.session,user_role=self.user_role).search(query=query)
