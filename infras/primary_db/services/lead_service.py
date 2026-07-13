from . import BaseServiceModel
from ..models.leads import Leads
from core.utils.uuid_generator import generate_uuid
from ..repos.lead_repo import LeadsRepo
from .activity_log_service import ActivityLogService
from sqlalchemy import select, delete, update, or_, func,String
from sqlalchemy.ext.asyncio import AsyncSession
from icecream import ic
from core.data_formats.enums.user_enums import UserRoles
from math import ceil
from datetime import datetime
from typing import Optional
from schemas.db_schemas.lead import AddLeadDbSchema,UpdateLeadDbSchema
from schemas.request_schemas.lead import AddLeadSchema,UpdateLeadSchema
from core.decorators.error_handler_dec import catch_errors
from models.response_models.req_res_models import SuccessResponseTypDict,BaseResponseTypDict,ErrorResponseTypDict
from ..models.ui_id import TablesUiLId
from core.utils.ui_id_generator import generate_ui_id
from core.constants import UI_ID_STARTING_DIGIT,LUI_ID_LEAD_PREFIX,LUI_ID_OPPOR_PREFIX


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
        lui_id:str=(await self.session.execute(select(TablesUiLId.lead_luiid))).scalar_one_or_none()
        cur_uiid=generate_ui_id(prefix=LUI_ID_LEAD_PREFIX,last_id=lui_id)
        result = await lead_obj.add(data=AddLeadDbSchema(**data.model_dump(),id=lead_id,ui_id=cur_uiid,lui_id=lui_id))
        if result and not isinstance(result, dict) or (isinstance(result, dict) and result.get("success") is not False):
            await ActivityLogService(self.session, self.user_role, self.cur_user_id).log_action(
                action="CREATE_MANUAL",
                entity_type="LEAD",
                entity_id=lead_id,
                details={"name": data.name, "email": data.email}
            )
        return result
    
    @catch_errors
    async def update(self,data:UpdateLeadSchema):
        data_toupdate=data.model_dump(exclude_none=True,exclude_unset=True)
        if not data_toupdate or len(data_toupdate)<1:
            return ErrorResponseTypDict(status_code=400,success=False,msg="Error : Updating Lead",description="No valid fields to update provided")
        
        from sqlalchemy import select
        from ..models.leads import Leads
        from fastapi.encoders import jsonable_encoder
        old_record = (await self.session.execute(select(Leads).where(Leads.id == data.lead_id))).scalar_one_or_none()
        old_values = {}
        new_values = {}
        if old_record:
            for key, new_val in data_toupdate.items():
                if not hasattr(old_record, key):
                    continue
                old_val_raw = getattr(old_record, key)
                old_val = jsonable_encoder(old_val_raw)
                if old_val != new_val:
                    old_values[key] = old_val if old_val is not None else None
                    new_values[key] = new_val if new_val is not None else None

        result = await LeadsRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).update(data=UpdateLeadDbSchema(**data_toupdate))
        if result and not isinstance(result, dict) or (isinstance(result, dict) and result.get("success") is not False):
            details = {"updated_fields": list(data_toupdate.keys())}
            if old_values or new_values:
                details["old_values"] = old_values
                details["new_values"] = new_values

            await ActivityLogService(self.session, self.user_role, self.cur_user_id).log_action(
                action="UPDATE",
                entity_type="LEAD",
                entity_id=data.lead_id,
                details=details
            )
        return result

    @catch_errors
    async def delete(self, lead_id: str, soft_delete: bool = True):
        result = await LeadsRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).delete(lead_id=lead_id, soft_delete=soft_delete)
        if result and not isinstance(result, dict) or (isinstance(result, dict) and result.get("success") is not False):
            await ActivityLogService(self.session, self.user_role, self.cur_user_id).log_action(
                action="DELETE",
                entity_type="LEAD",
                entity_id=lead_id,
                details={"soft_delete": soft_delete}
            )
        return result
    
    @catch_errors  
    async def recover(self, lead_id: str):
        result = await LeadsRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).recover(lead_id=lead_id)
        if result and not isinstance(result, dict) or (isinstance(result, dict) and result.get("success") is not False):
            await ActivityLogService(self.session, self.user_role, self.cur_user_id).log_action(
                action="RECOVER",
                entity_type="LEAD",
                entity_id=lead_id
            )
        return result

    @catch_errors
    async def get(self, cursor: int = 1, limit: int = 10, query: str = "",include_deleted:Optional[bool]=False):
        return await LeadsRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).get(cursor=cursor,limit=limit,query=query,include_deleted=include_deleted)

    @catch_errors
    async def get_by_id(self, lead_id: str):
        return await LeadsRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).get_by_id(lead_id=lead_id)
    
    @catch_errors
    async def search(self, query: str, offset: int = 0):
        return await LeadsRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).search(query=query,offset=offset)

    @catch_errors
    async def convert_to_opportunity(self, lead_id: str):
        from ..repos.opportunity_repo import OpportunitiesRepo
        from schemas.db_schemas.opportunity import CreateOpportunityDbSchema
        from core.data_formats.enums.lead_oppr_enums import LeadStatus, OpportunityStatus

        lead_repo = LeadsRepo(session=self.session, user_role=self.user_role, cur_user_id=self.cur_user_id)
        
        # Check if lead exists
        lead = await lead_repo.get_lead_raw(lead_id=lead_id)
        if not lead:
            return ErrorResponseTypDict(status_code=404, success=False, msg="Error : Converting Lead", description="Lead not found")
        
        # Check if lead is already converted
        if lead.status == LeadStatus.CONVERTED.value:
            return ErrorResponseTypDict(status_code=400, success=False, msg="Error : Converting Lead", description="Lead is already converted to an opportunity")
        
        # Check if opportunity already exists for this lead
        oppor_repo = OpportunitiesRepo(session=self.session, user_role=self.user_role, cur_user_id=self.cur_user_id)
        if await oppor_repo.is_opportunity_exists(lead_id=lead_id):
            return ErrorResponseTypDict(status_code=400, success=False, msg="Error : Converting Lead", description="An opportunity already exists for this lead")
        
        # Create opportunity
        oppr_id = generate_uuid()
        lui_id = (await self.session.execute(select(TablesUiLId.oppor_luiid))).scalar_one_or_none()
        cur_uiid = generate_ui_id(prefix=LUI_ID_OPPOR_PREFIX, last_id=lui_id)
        
        oppor_data = CreateOpportunityDbSchema(
            id=oppr_id,
            ui_id=cur_uiid,
            lead_id=lead_id,
            name=f"{lead.name} - Opportunity",
            product="",
            billing_type="ONE_TIME",
            deal_value=0,
            description=lead.description or "",
            status=OpportunityStatus.OPEN.value
        )
        
        add_result = await oppor_repo.add(data=oppor_data)
        if not add_result or isinstance(add_result, ErrorResponseTypDict):
            return add_result or ErrorResponseTypDict(status_code=400, success=False, msg="Error : Converting Lead", description="Failed to create opportunity")
        
        # Update lead status to CONVERTED
        await lead_repo.update_status(lead_id=lead_id, status=LeadStatus.CONVERTED.value)
        
        await ActivityLogService(self.session, self.user_role, self.cur_user_id).log_action(
            action="CONVERTED_TO_OPPORTUNITY",
            entity_type="LEAD",
            entity_id=lead_id,
            details={"opportunity_id": oppr_id}
        )
        return True
