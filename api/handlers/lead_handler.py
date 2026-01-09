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
from .  import HTTPException,ErrorResponseTypDict,SuccessResponseTypDict,BaseResponseTypDict
from core.utils.mob_no_validator import mobile_number_validator


class HandleLeadsRequest:
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
    async def add(self,data:AddLeadSchema):
        if not mobile_number_validator(mob_no=data.phone):
            raise HTTPException(
                status_code=400,
                detail=ErrorResponseTypDict(
                    status_code=400,
                    success=False,
                    msg="Error : Creating lead ",
                    description="Invalid input data, May be its a mobile number"
                )
            )
        
        res = await LeadsService(session=self.session,user_role=self.user_role).add(data=data)
        if res:
            return SuccessResponseTypDict(
            detail=BaseResponseTypDict(
                status_code=200,
                success=True,
                msg="Lead created successfully"
            )
        )
    
    @catch_errors
    async def update(self,data:UpdateLeadSchema):
        if not mobile_number_validator(mob_no=data.phone):
            raise HTTPException(
                status_code=400,
                detail=ErrorResponseTypDict(
                    status_code=400,
                    success=False,
                    msg="Error : Creating lead ",
                    description="Invalid input data, May be its a mobile number"
                )
            )
        res = await LeadsService(session=self.session,user_role=self.user_role).update(data=data)
        if not res:
            raise HTTPException(
                status_code=400,
                detail=ErrorResponseTypDict(
                    status_code=400,
                    success=False,
                    msg="Error : Updaing lead",
                    description="Invalid user input"
                )
            )
        
        return SuccessResponseTypDict(
            detail=BaseResponseTypDict(
                status_code=200,
                success=True,
                msg="Lead updated successfully"
            )
        )

    @catch_errors
    async def delete(self, lead_id: str):
        res = await LeadsService(session=self.session,user_role=self.user_role).delete(lead_id=lead_id)
        if not res:
            raise HTTPException(
                status_code=400,
                detail=ErrorResponseTypDict(
                    status_code=400,
                    success=False,
                    msg="Error : Deleting lead",
                    description="Invalid user input"
                )
            )
        
        return SuccessResponseTypDict(
            detail=BaseResponseTypDict(
                status_code=200,
                success=True,
                msg="Lead deleted successfully"
            )
        )
    
    @catch_errors
    async def get(self, offset: int = 1, limit: int = 10, query: str = ""):
        return await LeadsService(session=self.session,user_role=self.user_role).get(offset=offset,limit=limit,query=query)

    @catch_errors
    async def get_by_id(self, lead_id: str):
        return await LeadsService(session=self.session,user_role=self.user_role).get_by_id(lead_id=lead_id)
    
    @catch_errors
    async def search(self, query: str):
        return await LeadsService(session=self.session,user_role=self.user_role).search(query=query)
