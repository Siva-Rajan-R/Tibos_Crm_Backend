from infras.primary_db.services.opportunity_service import OpportunitiesService
from sqlalchemy import select, delete, update,func,or_,String
from sqlalchemy.ext.asyncio import AsyncSession
from icecream import ic
from core.data_formats.enums.common_enums import UserRoles
from typing import Optional
from core.data_formats.enums.pg_enums import OpportunityStatus,LeadSource,LeadStatus,BillingType
from schemas.db_schemas.opportunity import CreateOpportunityDbSchema,UpdateOpportunityDbSchema
from schemas.request_schemas.opportunity import CreateOpportunitySchema,UpdateOpportunitySchema,RecoverOpportunitySchema
from core.utils.uuid_generator import generate_uuid
from core.decorators.error_handler_dec import catch_errors
from . import HTTPException,ErrorResponseTypDict,SuccessResponseTypDict,BaseResponseTypDict
from datetime import datetime
from math import ceil


class HandleOpportunitiesRequest:
    def __init__(self, session: AsyncSession, user_role: UserRoles,cur_user_id:str):
        self.session = session
        self.user_role = user_role
        self.cur_user_id=cur_user_id

        if isinstance(self.user_role,UserRoles):
            self.user_role=self.user_role.value

        if self.user_role== UserRoles.USER.value:
            raise HTTPException(
                status_code=401,
                detail=ErrorResponseTypDict(
                    msg="Error : ",
                    description="Insufficient permission",
                    status_code=401,
                    success=False
                ).model_dump(mode='json')
            )
    
    @catch_errors
    async def add(self,data:CreateOpportunitySchema):
        res= await OpportunitiesService(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).add(data=data)
        if not res or isinstance(res,ErrorResponseTypDict):
            detail:ErrorResponseTypDict=ErrorResponseTypDict(
                    status_code=400,
                    msg="Error : Creating Opportunity",
                    description="A Unknown Error, Please Try Again Later!"
                ) if not isinstance(res,ErrorResponseTypDict) else res
            
            raise HTTPException(
                status_code=detail.status_code,
                detail=detail.model_dump(mode='json')
            )
        return SuccessResponseTypDict(
            detail=BaseResponseTypDict(
                status_code=200,
                success=True,
                msg="Opportunity created successfully"
            )
        )

    @catch_errors
    async def update(self,data:UpdateOpportunitySchema):
        res=await OpportunitiesService(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).update(data=data)
        if not res or isinstance(res,ErrorResponseTypDict):
            detail:ErrorResponseTypDict=ErrorResponseTypDict(
                    status_code=400,
                    msg="Error : Updating Opportunity",
                    description="A Unknown Error, Please Try Again Later!"
                ) if not isinstance(res,ErrorResponseTypDict) else res
            
            raise HTTPException(
                status_code=detail.status_code,
                detail=detail.model_dump(mode='json')
            )
        
        return SuccessResponseTypDict(
            detail=BaseResponseTypDict(
                status_code=200,
                success=True,
                msg="Opportunity updated successfully"
            )
        )

    @catch_errors
    async def delete(self, opportunity_id: str, soft_delete: bool = True):
        res = await OpportunitiesService(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).delete(opportunity_id=opportunity_id,soft_delete=soft_delete)
        if not res or isinstance(res,ErrorResponseTypDict):
            detail:ErrorResponseTypDict=ErrorResponseTypDict(
                    status_code=400,
                    msg="Error : Deleting Opportunity",
                    description="A Unknown Error, Please Try Again Later!"
                ) if not isinstance(res,ErrorResponseTypDict) else res
            
            raise HTTPException(
                status_code=detail.status_code,
                detail=detail.model_dump(mode='json')
            )
        
        return SuccessResponseTypDict(
            detail=BaseResponseTypDict(
                status_code=200,
                success=True,
                msg="Opportunity deleted successfully"
            )
        )
    
    @catch_errors
    async def recover(self, data:RecoverOpportunitySchema):
        res = await OpportunitiesService(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).recover(opportunity_id=data.opportunity_id)
        if not res or isinstance(res,ErrorResponseTypDict):
            detail:ErrorResponseTypDict=ErrorResponseTypDict(
                    status_code=400,
                    msg="Error : Recovering Opportunity",
                    description="A Unknown Error, Please Try Again Later!"
                ) if not isinstance(res,ErrorResponseTypDict) else res
            
            raise HTTPException(
                status_code=detail.status_code,
                detail=detail.model_dump(mode='json')
            )
        
        return SuccessResponseTypDict(
            detail=BaseResponseTypDict(
                status_code=200,
                success=True,
                msg="Opportunity recovered successfully"
            )
        )

    @catch_errors
    async def get(self, offset: int = 1, limit: int = 10, query: str = ""):
        return await OpportunitiesService(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).get(offset=offset,limit=limit,query=query)
            
    @catch_errors
    async def get_by_lead(self, lead_id: str):
        return await OpportunitiesService(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).get_by_lead(lead_id=lead_id)
    
    @catch_errors
    async def search(self, query: str):
        return await OpportunitiesService(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).search(query=query)
        
    @catch_errors
    async def get_by_id(self, opportunity_id:str):
        return await OpportunitiesService(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).get_by_id(opportunity_id=opportunity_id)
