from . import HTTPException,BaseRepoModel
from ..models.leads import Leads
from core.utils.uuid_generator import generate_uuid
from sqlalchemy import select, delete, update, or_, func,String
from sqlalchemy.ext.asyncio import AsyncSession
from icecream import ic
from core.data_formats.enums.user_enums import UserRoles
from math import ceil
from datetime import datetime
from typing import Optional
from schemas.db_schemas.lead import AddLeadDbSchema,UpdateLeadDbSchema
from core.decorators.db_session_handler_dec import start_db_transaction
from pydantic import EmailStr
from ..models.user import Users
from models.response_models.req_res_models import SuccessResponseTypDict,BaseResponseTypDict,ErrorResponseTypDict
from ..models.ui_id import TablesUiLId


class LeadsRepo(BaseRepoModel):
    def __init__(self, session: AsyncSession, user_role: UserRoles,cur_user_id:str):
        self.session = session
        self.user_role = user_role
        self.cur_user_id=cur_user_id
        self.leads_cols=(
            Leads.sequence_id,
            Leads.id.label("lead_id"),
            Leads.ui_id,
            Leads.name.label("lead_name"), 
            Leads.description.label("lead_description"),
            Leads.phone.label("lead_phone"),
            Leads.email.label("lead_email"),
            Leads.source.label("lead_source"),
            Leads.assigned_to.label("lead_assigned_to"),
            Leads.status.label("lead_status")
        )

    async def is_lead_exists(self,email:EmailStr,mobile_number:str):
        is_exists=(
            await self.session.execute(
                select(Leads.id)
                .where(
                    or_(
                        Leads.email==email,
                        Leads.phone==mobile_number
                    )
                )
            )
        ).scalar_one_or_none()

        return is_exists


    @start_db_transaction
    async def add(self,data:AddLeadDbSchema):
        self.session.add(Leads(**data.model_dump(exclude=['lui_id'])))
        await self.session.execute(update(TablesUiLId).where(TablesUiLId.id=="1").values(lead_luiid=data.ui_id))
        return True
    
    @start_db_transaction
    async def update(self,data:UpdateLeadDbSchema):
        data_toupdate=data.model_dump(exclude=['lead_id'],exclude_none=True,exclude_unset=True)
        if not data_toupdate or len(data_toupdate)<1:
            return ErrorResponseTypDict(status_code=400,success=False,msg="Error : Updating Lead",description="No valid fields to update provided")
        
        stmt = (
            update(Leads)
            .where(Leads.id == data.lead_id)
            .values(
                **data_toupdate
            )
            .returning(Leads.id)
        )

        is_updated = (await self.session.execute(stmt)).scalar_one_or_none()

        return is_updated if is_updated else ErrorResponseTypDict(status_code=400,success=False,msg="Error : Updating Lead",description="Unable to update the lead, may be invalid lead id or no changes in data")

    @start_db_transaction
    async def delete(self, lead_id: str, soft_delete: bool = True):
        if soft_delete:
            stmt = (
                update(Leads)
                .where(Leads.id == lead_id, Leads.is_deleted == False)
                .values(
                    is_deleted=True,
                    deleted_at=func.now(),
                    deleted_by=self.cur_user_id
                )
                .returning(Leads.id)
            )
            is_deleted = (await self.session.execute(stmt)).scalar_one_or_none()
        else:
            if self.user_role if isinstance(self.user_role,UserRoles) else self.user_role!=UserRoles.SUPER_ADMIN.value:
                return ErrorResponseTypDict(status_code=403,success=False,msg="Error : Deleting Lead",description="Only super admin can perform hard delete operation")
            stmt = delete(Leads).where(Leads.id == lead_id).returning(Leads.id)
            is_deleted = (await self.session.execute(stmt)).scalar_one_or_none()

        return is_deleted if is_deleted else ErrorResponseTypDict(status_code=400,success=False,msg="Error : Deleting Lead",description="Unable to delete the lead, may be invalid lead id or lead already deleted")
    
    @start_db_transaction
    async def recover(self, lead_id: str):
        if self.user_role if isinstance(self.user_role,UserRoles) else self.user_role!=UserRoles.SUPER_ADMIN.value:
            return ErrorResponseTypDict(status_code=403,success=False,msg="Error : Recovering Lead",description="Only super admin can perform recover operation")
        
        stmt = (
            update(Leads)
            .where(Leads.id == lead_id, Leads.is_deleted == True)
            .values(is_deleted=False)
            .returning(Leads.id)
        )
        is_recovered = (await self.session.execute(stmt)).scalar_one_or_none()
        return is_recovered if is_recovered else ErrorResponseTypDict(status_code=400,success=False,msg="Error : Recovering Lead",description="Unable to recover the lead, may lead is not deleted or already recovered")
    

    async def get(self, cursor: int = 1, limit: int = 10, query: str = "",include_deleted:bool=False):
        search = f"%{query.lower()}%"
        cursor=0 if cursor==1 else cursor
        date_expr=func.date(func.timezone("Asia/Kolkata",Leads.created_at))
        follwup_expr=func.date(func.timezone("Asia/Kolkata",Leads.next_followup))
        lastcont_expr=func.date(func.timezone("Asia/Kolkata",Leads.last_contacted))
        deleted_at=func.date(func.timezone("Asia/Kolkata",Leads.deleted_at))

        cols=[*self.leads_cols]
        if include_deleted:
            cols.extend([Users.name.label('deleted_by'),deleted_at.label('deleted_at')])

        leads = (
            await self.session.execute(
                select(
                    *cols,
                    lastcont_expr.label("lead_last_contacted"),
                    follwup_expr.label("lead_next_followup"),
                    date_expr.label("lead_created_at")
                )
                .join(Users,Users.id==Leads.deleted_by,isouter=True)
                .where(
                    or_(
                        Leads.id.ilike(search),
                        Leads.ui_id.ilike(search),
                        Leads.name.ilike(search),
                        Leads.phone.ilike(search),
                        Leads.email.ilike(search),
                        Leads.source.ilike(search),
                        Leads.status.ilike(search),
                        Leads.description.ilike(search),
                        func.cast(Leads.created_at,String).ilike(search)
                    ),
                    Leads.sequence_id > cursor,
                    Leads.is_deleted==include_deleted
                )
                .limit(limit)
                .order_by(Leads.sequence_id.asc())
            )
        ).mappings().all()

        if cursor==0:
            total = (
                await self.session.execute(select(func.count(Leads.id)))
            ).scalar_one()

        return {
            "leads": leads,
            "total_leads": total,
            "total_pages": ceil(total / limit),
            'next_cursor':leads[-1]['sequence_id'] if len(leads)>1 else None
        }

    async def get_by_id(self, lead_id: str):
        date_expr=func.date(func.timezone("Asia/Kolkata",Leads.created_at))
        follwup_expr=func.date(func.timezone("Asia/Kolkata",Leads.next_followup))
        lastcont_expr=func.date(func.timezone("Asia/Kolkata",Leads.last_contacted))
        lead = (
            await self.session.execute(
                select( 
                    *self.leads_cols,
                    follwup_expr.label("lead_next_followup"),
                    lastcont_expr.label("lead_last_contacted"),
                    date_expr.label("lead_created_at")
                ).where(or_(Leads.id == lead_id,Leads.ui_id==lead_id),Leads.is_deleted==False)
            )
        ).mappings().one_or_none()

        return {"lead": lead}
    

    async def search(self, query: str):
        search = f"%{query.lower()}%"

        result = await self.session.execute(
            select(
                Leads.id.label("lead_id"),
                Leads.name.label("lead_name"),
                Leads.phone.label("lead_phone"),
                Leads.email.label("lead_email"),
                Leads.source.label("lead_source"),
                Leads.assigned_to.label("lead_assigned_to"),
                Leads.status.label("lead_status"),
                Leads.next_followup.label("lead_next_followup"),
            )
            .where(
                or_(
                    Leads.id.ilike(search),
                    Leads.ui_id.ilike(search),
                    Leads.name.ilike(search),
                    Leads.phone.ilike(search),
                    Leads.email.ilike(search),
                    Leads.source.ilike(search),
                    Leads.status.ilike(search),
                    Leads.description.ilike(search)
                ),
                Leads.is_deleted==False
            )
            .limit(5)
        )

        leads = result.mappings().all()

        return {"leads": leads}
