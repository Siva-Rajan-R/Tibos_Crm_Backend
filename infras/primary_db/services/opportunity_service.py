from . import BaseServiceModel
from ..models.opportunity import Opportunities
from ..repos.opportunity_repo import OpportunitiesRepo
from ..repos.lead_repo import LeadsRepo
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
from models.response_models.req_res_models import SuccessResponseTypDict,BaseResponseTypDict,ErrorResponseTypDict


class OpportunitiesService(BaseServiceModel):
    def __init__(self, session: AsyncSession, user_role: UserRoles,cur_user_id:str):
        self.session = session
        self.user_role = user_role
        self.cur_user_id=cur_user_id
    
    @catch_errors
    async def add(self,data:CreateOpportunitySchema):
        # need check the lead is already exists on Opprtunity
        # and to check the given lead id is exists or not 

        oppor_obj=OpportunitiesRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id)
        if (await oppor_obj.is_opportunity_exists(lead_id=data.lead_id)):
            return ErrorResponseTypDict(status_code=400,success=False,msg="Error : Adding Opportunity",description="Opportunity with the given lead id already exists")
        
        is_lead_exists=await LeadsRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).get_by_id(lead_id=data.lead_id)
        if not is_lead_exists or len(is_lead_exists)<1:
            return ErrorResponseTypDict(status_code=400,success=False,msg="Error : Adding Opportunity",description="Lead with the given id does not exist")
        
        
        oppr_id:str=generate_uuid()
        return await OpportunitiesRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).add(data=CreateOpportunityDbSchema(**data.model_dump(mode='json'),id=oppr_id))


    @catch_errors
    async def update(self,data:UpdateOpportunitySchema):
        data_toupdate=data.model_dump(mode='json',exclude_none=True,exclude_unset=True)
        if not data_toupdate or len(data_toupdate)<1:
            return ErrorResponseTypDict(status_code=400,success=False,msg="Error : Updating Opportunity",description="No valid fields to update provided")
        
        return await OpportunitiesRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).update(data=UpdateOpportunityDbSchema(**data_toupdate))

    @catch_errors
    async def delete(self, opportunity_id: str,soft_delete: bool = True):
        return await OpportunitiesRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).delete(opportunity_id=opportunity_id,soft_delete=soft_delete)

    @catch_errors  
    async def recover(self, opportunity_id: str):
        return await OpportunitiesRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).recover(opportunity_id=opportunity_id)
    
    @catch_errors
    async def get(self, offset: int = 1, limit: int = 10, query: str = "",include_deleted:Optional[bool]=False):
        return await OpportunitiesRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).get(offset=offset,limit=limit,query=query,include_deleted=include_deleted)
            
    @catch_errors
    async def get_by_lead(self, lead_id: str):
        return await OpportunitiesRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).get_by_lead(lead_id=lead_id)
    
    @catch_errors
    async def search(self, query: str):
        return await OpportunitiesRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).search(query=query)
        
    @catch_errors
    async def get_by_id(self, opportunity_id:str):
        return await OpportunitiesRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).get_by_id(opportunity_id=opportunity_id)
