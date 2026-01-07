from . import BaseServiceModel
from ..models.opportunity import Opportunities
from ..repos.opportunity_repo import OpportunitiesRepo
from ..models.leads import Leads
from sqlalchemy import select, delete, update,func,or_,String
from sqlalchemy.ext.asyncio import AsyncSession
from icecream import ic
from core.data_formats.enums.common_enums import UserRoles
from typing import Optional
from core.data_formats.enums.pg_enums import OpportunityStatus,LeadSource,LeadStatus,BillingType
from schemas.db_schemas.opportunity import CreateOpportunityDbSchema,UpdateOpportunityDbSchema
from schemas.request_schemas.opportunity import CreateOpportunitySchema,UpdateOpportunitySchema
from core.utils.uuid_generator import generate_uuid
from core.decorators.error_handler_dec import catch_errors
from datetime import datetime
from math import ceil


class OpportunitiesService(BaseServiceModel):
    def __init__(self, session: AsyncSession, user_role: UserRoles):
        self.session = session
        self.user_role = user_role
    
    @catch_errors
    async def add(self,data:CreateOpportunitySchema):
        oppr_id:str=generate_uuid()
        return await OpportunitiesRepo(session=self.session,user_role=self.user_role).add(data=CreateOpportunityDbSchema(**data.model_dump(mode='json'),id=oppr_id))

    @catch_errors
    async def update(self,data:UpdateOpportunitySchema):
        data_toupdate=data.model_dump(mode='json',exclude_none=True,exclude_unset=True)
        if not data_toupdate or len(data_toupdate)<1:
            return False
        
        return await OpportunitiesRepo(session=self.session,user_role=self.user_role).update(data=UpdateOpportunityDbSchema(**data_toupdate))

    @catch_errors
    async def delete(self, opportunity_id: str):
        return await OpportunitiesRepo(session=self.session,user_role=self.user_role).delete(opportunity_id=opportunity_id)

    @catch_errors
    async def get(self, offset: int = 1, limit: int = 10, query: str = ""):
        return await OpportunitiesRepo(session=self.session,user_role=self.user_role).get(offset=offset,limit=limit,query=query)
            
    @catch_errors
    async def get_by_lead(self, lead_id: str):
        return await OpportunitiesRepo(session=self.session,user_role=self.user_role).get_by_lead(lead_id=lead_id)
    
    @catch_errors
    async def search(self, query: str):
        return await OpportunitiesRepo(session=self.session,user_role=self.user_role).search(query=query)
        
    @catch_errors
    async def get_by_id(self, opportunity_id:str):
        return await OpportunitiesRepo(session=self.session,user_role=self.user_role).get_by_id(opportunity_id=opportunity_id)
