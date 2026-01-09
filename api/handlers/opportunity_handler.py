from infras.primary_db.services.opportunity_service import OpportunitiesService
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
from . import HTTPException,ErrorResponseTypDict,SuccessResponseTypDict,BaseResponseTypDict
from datetime import datetime
from math import ceil


class HandleOpportunitiesRequest:
    def __init__(self, session: AsyncSession, user_role: UserRoles):
        self.session = session
        self.user_role = user_role

        if self.user_role.value == UserRoles.USER.value:
            raise HTTPException(
                status_code=401,
                detail=ErrorResponseTypDict(
                    msg="Error : ",
                    description="Insufficient permission",
                    status_code=401,
                    success=False
                )
            )
    
    @catch_errors
    async def add(self,data:CreateOpportunitySchema):
        res= await OpportunitiesService(session=self.session,user_role=self.user_role).add(data=data)
        if res:
            return SuccessResponseTypDict(
            detail=BaseResponseTypDict(
                status_code=200,
                success=True,
                msg="Opportunity created successfully"
            )
        )

    @catch_errors
    async def update(self,data:UpdateOpportunitySchema):
        res=await OpportunitiesService(session=self.session,user_role=self.user_role).update(data=data)
        if not res:
            raise HTTPException(
                status_code=400,
                detail=ErrorResponseTypDict(
                    status_code=400,
                    success=False,
                    msg="Error : Updaing Opportunity",
                    description="Invalid user input"
                )
            )
        
        return SuccessResponseTypDict(
            detail=BaseResponseTypDict(
                status_code=200,
                success=True,
                msg="Opportunity updated successfully"
            )
        )

    @catch_errors
    async def delete(self, opportunity_id: str):
        res = await OpportunitiesService(session=self.session,user_role=self.user_role).delete(opportunity_id=opportunity_id)
        if not res:
            raise HTTPException(
                status_code=400,
                detail=ErrorResponseTypDict(
                    status_code=400,
                    success=False,
                    msg="Error : Deleting opportunity",
                    description="Invalid user input"
                )
            )
        
        return SuccessResponseTypDict(
            detail=BaseResponseTypDict(
                status_code=200,
                success=True,
                msg="Opportunity deleted successfully"
            )
        )

    @catch_errors
    async def get(self, offset: int = 1, limit: int = 10, query: str = ""):
        return await OpportunitiesService(session=self.session,user_role=self.user_role).get(offset=offset,limit=limit,query=query)
            
    @catch_errors
    async def get_by_lead(self, lead_id: str):
        return await OpportunitiesService(session=self.session,user_role=self.user_role).get_by_lead(lead_id=lead_id)
    
    @catch_errors
    async def search(self, query: str):
        return await OpportunitiesService(session=self.session,user_role=self.user_role).search(query=query)
        
    @catch_errors
    async def get_by_id(self, opportunity_id:str):
        return await OpportunitiesService(session=self.session,user_role=self.user_role).get_by_id(opportunity_id=opportunity_id)
