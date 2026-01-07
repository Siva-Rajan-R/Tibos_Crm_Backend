from . import HTTPException,BaseRepoModel
from ..models.leads import Leads
from core.utils.uuid_generator import generate_uuid
from sqlalchemy import select, delete, update, or_, func,String
from sqlalchemy.ext.asyncio import AsyncSession
from icecream import ic
from core.data_formats.enums.common_enums import UserRoles
from core.data_formats.enums.pg_enums import OpportunityStatus,LeadSource,LeadStatus
from math import ceil
from datetime import datetime
from typing import Optional
from schemas.db_schemas.lead import AddLeadDbSchema,UpdateLeadDbSchema
from core.decorators.db_session_handler_dec import start_db_transaction


class LeadsRepo(BaseRepoModel):
    def __init__(self, session: AsyncSession, user_role: UserRoles):
        self.session = session
        self.user_role = user_role
        self.leads_cols=(
            Leads.id.label("lead_id"),
            Leads.name.label("lead_name"), 
            Leads.description.label("lead_description"),
            Leads.phone.label("lead_phone"),
            Leads.email.label("lead_email"),
            Leads.source.label("lead_source"),
            Leads.assigned_to.label("lead_assigned_to"),
            Leads.status.label("lead_status")
        )


    @start_db_transaction
    async def add(self,data:AddLeadDbSchema):
        self.session.add(Leads(**data.model_dump()))
        return True
    
    @start_db_transaction
    async def update(self,data:UpdateLeadDbSchema):
        data_toupdate=data.model_dump(exclude=['lead_id'],exclude_none=True,exclude_unset=True)
        if not data_toupdate or len(data_toupdate)<1:
            return False
        
        stmt = (
            update(Leads)
            .where(Leads.id == data.lead_id)
            .values(
                **data_toupdate
            )
            .returning(Leads.id)
        )

        is_updated = (await self.session.execute(stmt)).scalar_one_or_none()

        return is_updated

    @start_db_transaction
    async def delete(self, lead_id: str):
        stmt = delete(Leads).where(Leads.id == lead_id).returning(Leads.id)
        is_deleted = (await self.session.execute(stmt)).scalar_one_or_none()

        return is_deleted
    

    async def get(self, offset: int = 1, limit: int = 10, query: str = ""):
        cursor = (offset - 1) * limit
        search = f"%{query.lower()}%"
        date_expr=func.date(func.timezone("Asia/Kolkata",Leads.created_at))
        follwup_expr=func.date(func.timezone("Asia/Kolkata",Leads.next_followup))
        lastcont_expr=func.date(func.timezone("Asia/Kolkata",Leads.last_contacted))

        leads = (
            await self.session.execute(
                select(
                    *self.leads_cols,
                    lastcont_expr.label("lead_last_contacted"),
                    follwup_expr.label("lead_next_followup"),
                    date_expr.label("lead_created_at")
                )
                .where(
                    or_(
                        Leads.id.ilike(search),
                        Leads.name.ilike(search),
                        Leads.phone.ilike(search),
                        Leads.email.ilike(search),
                        Leads.source.ilike(search),
                        Leads.status.ilike(search),
                        Leads.description.ilike(search),
                        func.cast(Leads.created_at,String).ilike(search)
                    ),
                    Leads.sequence_id > cursor
                )
                .limit(limit)
            )
        ).mappings().all()

        total = (
            await self.session.execute(select(func.count(Leads.id)))
        ).scalar_one()

        return {
            "leads": leads,
            "total_leads": total,
            "total_pages": ceil(total / limit)
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
                ).where(Leads.id == lead_id)
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
                    Leads.name.ilike(search),
                    Leads.phone.ilike(search),
                    Leads.email.ilike(search),
                    Leads.source.ilike(search),
                    Leads.status.ilike(search),
                    Leads.description.ilike(search)
                )
            )
            .limit(5)
        )

        leads = result.mappings().all()

        return {"leads": leads}
