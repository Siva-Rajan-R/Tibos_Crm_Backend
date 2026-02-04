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
from schemas.request_schemas.lead import AddLeadSchema,UpdateLeadSchema,RecoverLeadSchema
from core.decorators.error_handler_dec import catch_errors
from .  import HTTPException,ErrorResponseTypDict,SuccessResponseTypDict,BaseResponseTypDict
from core.utils.mob_no_validator import mobile_number_validator


class HandleLeadsRequest:
    def __init__(self, session: AsyncSession, user_role: UserRoles,cur_user_id:str):
        self.session = session
        self.user_role = user_role
        self.cur_user_id=cur_user_id

        # if isinstance(self.user_role,UserRoles):
        #     self.user_role=self.user_role.value

        # if self.user_role== UserRoles.USER.value:
        #     raise HTTPException(
        #         status_code=401,
        #         detail=ErrorResponseTypDict(
        #             msg="Error : ",
        #             description="Insufficient permission",
        #             status_code=401,
        #             success=False
        #         ).model_dump(mode='json')
        #     )

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
                ).model_dump(mode='json')
            )
        
        res = await LeadsService(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).add(data=data)
        if not res or isinstance(res,ErrorResponseTypDict):
            detail:ErrorResponseTypDict=ErrorResponseTypDict(
                    status_code=400,
                    msg="Error : Creating Lead",
                    description="A Unknown Error, Please Try Again Later!",
                    success=False
                ) if not isinstance(res,ErrorResponseTypDict) else res
            
            raise HTTPException(
                status_code=detail.status_code,
                detail=detail.model_dump(mode='json')
            )
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
                ).model_dump(mode='json')
            )
        res = await LeadsService(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).update(data=data)
        if not res or isinstance(res,ErrorResponseTypDict):
            detail:ErrorResponseTypDict=ErrorResponseTypDict(
                    status_code=400,
                    msg="Error : Updating Lead",
                    description="A Unknown Error, Please Try Again Later!",
                    success=False
                ) if not isinstance(res,ErrorResponseTypDict) else res
            
            raise HTTPException(
                status_code=detail.status_code,
                detail=detail.model_dump(mode='json')
            )
        
        return SuccessResponseTypDict(
            detail=BaseResponseTypDict(
                status_code=200,
                success=True,
                msg="Lead updated successfully"
            )
        )

    @catch_errors
    async def delete(self, lead_id: str, soft_delete: bool = True):
        res = await LeadsService(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).delete(lead_id=lead_id,soft_delete=soft_delete)
        if not res or isinstance(res,ErrorResponseTypDict):
            detail:ErrorResponseTypDict=ErrorResponseTypDict(
                    status_code=400,
                    msg="Error : Deleting Lead",
                    description="A Unknown Error, Please Try Again Later!",
                    success=False
                ) if not isinstance(res,ErrorResponseTypDict) else res
            
            raise HTTPException(
                status_code=detail.status_code,
                detail=detail.model_dump(mode='json')
            )
        
        return SuccessResponseTypDict(
            detail=BaseResponseTypDict(
                status_code=200,
                success=True,
                msg="Lead deleted successfully"
            )
        )
    
    @catch_errors
    async def recover(self, data:RecoverLeadSchema):      
        res = await LeadsService(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).recover(lead_id=data.lead_id)
        if not res or isinstance(res,ErrorResponseTypDict):
            detail:ErrorResponseTypDict=ErrorResponseTypDict(
                    status_code=400,
                    msg="Error : Recovering Lead",
                    description="A Unknown Error, Please Try Again Later!",
                    success=False
                ) if not isinstance(res,ErrorResponseTypDict) else res
            
            raise HTTPException(
                status_code=detail.status_code,
                detail=detail.model_dump(mode='json')
            )
        
        return SuccessResponseTypDict(
            detail=BaseResponseTypDict(
                status_code=200,
                success=True,
                msg="Lead recovered successfully"
            )
        )
    
    @catch_errors
    async def get(self, cursor: int = 1, limit: int = 10, query: str = ""):
        if cursor is None:
            raise HTTPException(
                status_code=400,
                detail=ErrorResponseTypDict(
                    status_code=400,
                    description="No more datas found for leads",
                    msg="Error : fetching leads",
                    success=False
                )
            )
        return await LeadsService(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).get(cursor=cursor,limit=limit,query=query)

    @catch_errors
    async def get_by_id(self, lead_id: str):
        return await LeadsService(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).get_by_id(lead_id=lead_id)
    
    @catch_errors
    async def search(self, query: str):
        return await LeadsService(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).search(query=query)
