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
from models.response_models.req_res_models import SuccessResponseTypDict,BaseResponseTypDict,ErrorResponseTypDict


class LeadsService(BaseServiceModel):
    def __init__(self, session: AsyncSession, user_role: UserRoles,cur_user_id:str):
        self.session = session
        self.user_role = user_role
        self.cur_user_id=cur_user_id


    @catch_errors
    async def add(self,data:AddLeadSchema):
        # Need to check the given emailor phone have exisiting leads
        lead_obj=LeadsRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id)
        if (await lead_obj.is_lead_exists(email=data.email,mobile_number=data.phone)):
            return ErrorResponseTypDict(status_code=400,success=False,msg="Error : Adding Lead",description="Lead with the given email or phone number already exists")
        
        lead_id:str=generate_uuid()
        return await lead_obj.add(data=AddLeadDbSchema(**data.model_dump(),id=lead_id))
    
    @catch_errors
    async def update(self,data:UpdateLeadSchema):
        data_toupdate=data.model_dump(exclude_none=True,exclude_unset=True)
        if not data_toupdate or len(data_toupdate)<1:
            return ErrorResponseTypDict(status_code=400,success=False,msg="Error : Updating Lead",description="No valid fields to update provided")
        
        return await LeadsRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).update(data=UpdateLeadDbSchema(**data_toupdate))

    @catch_errors
    async def delete(self, lead_id: str, soft_delete: bool = True):
        return await LeadsRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).delete(lead_id=lead_id, soft_delete=soft_delete)
    
    @catch_errors  
    async def recover(self, lead_id: str):
        return await LeadsRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).recover(lead_id=lead_id)

    @catch_errors
    async def get(self, offset: int = 1, limit: int = 10, query: str = "",include_deleted:Optional[bool]=False):
        return await LeadsRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).get(offset=offset,limit=limit,query=query,include_deleted=include_deleted)

    @catch_errors
    async def get_by_id(self, lead_id: str):
        return await LeadsRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).get_by_id(lead_id=lead_id)
    
    @catch_errors
    async def search(self, query: str):
        return await LeadsRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).search(query=query)
