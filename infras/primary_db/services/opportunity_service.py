from . import BaseServiceModel
from ..models.opportunity import Opportunities
from ..repos.opportunity_repo import OpportunitiesRepo
from ..repos.lead_repo import LeadsRepo
from ..models.leads import Leads
from .activity_log_service import ActivityLogService
from sqlalchemy import select, delete, update,func,or_,String
from sqlalchemy.ext.asyncio import AsyncSession
from icecream import ic
from core.data_formats.enums.user_enums import UserRoles
from typing import Optional
from schemas.db_schemas.opportunity import CreateOpportunityDbSchema,UpdateOpportunityDbSchema
from schemas.request_schemas.opportunity import CreateOpportunitySchema,UpdateOpportunitySchema
from core.utils.uuid_generator import generate_uuid
from core.decorators.error_handler_dec import catch_errors
from datetime import datetime
from math import ceil
from models.response_models.req_res_models import SuccessResponseTypDict,BaseResponseTypDict,ErrorResponseTypDict
from ..models.ui_id import TablesUiLId
from core.utils.ui_id_generator import generate_ui_id
from core.constants import UI_ID_STARTING_DIGIT,LUI_ID_OPPOR_PREFIX


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
        lui_id:str=(await self.session.execute(select(TablesUiLId.oppor_luiid))).scalar_one_or_none()
        cur_uiid=generate_ui_id(prefix=LUI_ID_OPPOR_PREFIX,last_id=lui_id)
        
        res = await OpportunitiesRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).add(data=CreateOpportunityDbSchema(**data.model_dump(mode='json'),id=oppr_id,ui_id=cur_uiid))
        
        if res and not isinstance(res, ErrorResponseTypDict):
            from core.data_formats.enums.lead_oppr_enums import LeadStatus
            await LeadsRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).update_status(lead_id=data.lead_id, status=LeadStatus.CONVERTED.value)
            await ActivityLogService(self.session, self.user_role, self.cur_user_id).log_action(
                action="CREATE_MANUAL",
                entity_type="OPPORTUNITY",
                entity_id=oppr_id,
                details={"name": data.name, "lead_id": data.lead_id}
            )
            
        return res


    @catch_errors
    async def update(self,data:UpdateOpportunitySchema):
        data_toupdate=data.model_dump(mode='json',exclude_none=True,exclude_unset=True)
        if not data_toupdate or len(data_toupdate)<1:
            return ErrorResponseTypDict(status_code=400,success=False,msg="Error : Updating Opportunity",description="No valid fields to update provided")
        
        result = await OpportunitiesRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).update(data=UpdateOpportunityDbSchema(**data_toupdate))
        if result and not isinstance(result, dict) or (isinstance(result, dict) and result.get("success") is not False):
            await ActivityLogService(self.session, self.user_role, self.cur_user_id).log_action(
                action="UPDATE",
                entity_type="OPPORTUNITY",
                entity_id=data.opportunity_id,
                details={"updated_fields": list(data_toupdate.keys())}
            )
        return result

    @catch_errors
    async def delete(self, opportunity_id: str,soft_delete: bool = True):
        result = await OpportunitiesRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).delete(opportunity_id=opportunity_id,soft_delete=soft_delete)
        if result and not isinstance(result, dict) or (isinstance(result, dict) and result.get("success") is not False):
            await ActivityLogService(self.session, self.user_role, self.cur_user_id).log_action(
                action="DELETE",
                entity_type="OPPORTUNITY",
                entity_id=opportunity_id,
                details={"soft_delete": soft_delete}
            )
        return result

    @catch_errors  
    async def recover(self, opportunity_id: str):
        result = await OpportunitiesRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).recover(opportunity_id=opportunity_id)
        if result and not isinstance(result, dict) or (isinstance(result, dict) and result.get("success") is not False):
            await ActivityLogService(self.session, self.user_role, self.cur_user_id).log_action(
                action="RECOVER",
                entity_type="OPPORTUNITY",
                entity_id=opportunity_id
            )
        return result
    
    @catch_errors
    async def get(self, cursor: int = 1, limit: int = 10, query: str = "",include_deleted:Optional[bool]=False):
        return await OpportunitiesRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).get(cursor=cursor,limit=limit,query=query,include_deleted=include_deleted)
            
    @catch_errors
    async def get_by_lead(self, lead_id: str):
        return await OpportunitiesRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).get_by_lead(lead_id=lead_id)
    
    @catch_errors
    async def search(self, query: str):
        return await OpportunitiesRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).search(query=query)
        
    @catch_errors
    async def get_by_id(self, opportunity_id:str):
        return await OpportunitiesRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).get_by_id(opportunity_id=opportunity_id)

    @catch_errors
    async def convert_to_customer(self, opportunity_id: str):
        from ..repos.customer_repo import CustomersRepo
        from ..models.customer import Customers
        from schemas.db_schemas.customer import AddCustomerDbSchema
        from core.data_formats.enums.lead_oppr_enums import OpportunityStatus
        from core.constants import LUI_ID_CUSTOMER_PREFIX

        oppor_repo = OpportunitiesRepo(session=self.session, user_role=self.user_role, cur_user_id=self.cur_user_id)
        
        # Fetch opportunity with lead data
        opp_data = await oppor_repo.get_opportunity_with_lead(opportunity_id=opportunity_id)
        if not opp_data:
            return ErrorResponseTypDict(status_code=404, success=False, msg="Error : Converting Opportunity", description="Opportunity not found")
        
        # Check if already won
        if opp_data['opportunity_status'] == OpportunityStatus.WON.value:
            return ErrorResponseTypDict(status_code=400, success=False, msg="Error : Converting Opportunity", description="Opportunity is already converted (WON)")
        
        # Create customer from lead data
        customer_repo = CustomersRepo(session=self.session, user_role=self.user_role, cur_user_id=self.cur_user_id)
        customer_id = generate_uuid()
        lui_id = (await self.session.execute(select(TablesUiLId.customer_luiid))).scalar_one_or_none()
        cur_uiid = generate_ui_id(prefix=LUI_ID_CUSTOMER_PREFIX, last_id=lui_id)
        
        customer_data = AddCustomerDbSchema(
            id=customer_id,
            ui_id=cur_uiid,
            lui_id=lui_id,
            name=opp_data['lead_name'],
            mobile_number=opp_data['lead_phone'],
            email=opp_data['lead_email'] or '',
            website_url=None,
            no_of_employee=1,
            gst_number=None,
            industry="General",
            sector="General",
            address={"address": "", "pincode": "", "city": "", "state": ""},
            owner=opp_data.get('lead_assigned_to', '') or '',
            tenant_id='',
            secondary_domain=None,
            is_active=True
        )
        
        add_result = await customer_repo.add(data=customer_data)
        if not add_result or isinstance(add_result, ErrorResponseTypDict):
            return add_result or ErrorResponseTypDict(status_code=400, success=False, msg="Error : Converting Opportunity", description="Failed to create customer")
        
        # Update opportunity status to WON
        await oppor_repo.update_status(opportunity_id=opportunity_id, status=OpportunityStatus.WON.value)
        
        await ActivityLogService(self.session, self.user_role, self.cur_user_id).log_action(
            action="CONVERTED_TO_CUSTOMER",
            entity_type="OPPORTUNITY",
            entity_id=opportunity_id,
            details={"customer_id": customer_id}
        )
        return {"customer_id": customer_id}
