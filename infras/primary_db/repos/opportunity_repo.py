from . import HTTPException,BaseRepoModel
from ..models.opportunity import Opportunities
from ..models.leads import Leads
from sqlalchemy import select, delete, update,func,or_,String
from sqlalchemy.ext.asyncio import AsyncSession
from icecream import ic
from core.data_formats.enums.common_enums import UserRoles
from typing import Optional
from core.data_formats.enums.pg_enums import OpportunityStatus,LeadSource,LeadStatus,BillingType
from schemas.db_schemas.opportunity import CreateOpportunityDbSchema,UpdateOpportunityDbSchema
from core.utils.uuid_generator import generate_uuid
from core.decorators.db_session_handler_dec import start_db_transaction
from datetime import datetime
from math import ceil


class OpportunitiesRepo(BaseRepoModel):
    def __init__(self, session: AsyncSession, user_role: UserRoles):
        self.session = session
        self.user_role = user_role
        self.oppr_cols=(
            Opportunities.id.label("opportunity_id"),
            Opportunities.name.label("opportunity_name"),
            Opportunities.product.label("opportunity_product"),
            Opportunities.status.label("opportunity_status"),
            Opportunities.deal_value.label("opportunity_deal_value"),
            Opportunities.billing_type.label("opportunity_billing_type"),
            Opportunities.description.label("opportunity_description")
        )

    
    @start_db_transaction
    async def add(self,data:CreateOpportunityDbSchema):
        self.session.add(Opportunities(**data.model_dump(mode='json')))
        return True


    @start_db_transaction
    async def update(self,data:UpdateOpportunityDbSchema):
        data_toupdate=data.model_dump(mode='json',exclude=['opportunity_id'],exclude_none=True,exclude_unset=True)
        if not data_toupdate or len(data_toupdate)<1:
            return False
        
        stmt = (
            update(Opportunities)
            .where(Opportunities.id == data.opportunity_id)
            .values(
                **data_toupdate
            )
            .returning(Opportunities.id)
        )

        is_updated = (await self.session.execute(stmt)).scalar_one_or_none()
        return is_updated


    @start_db_transaction
    async def delete(self, opportunity_id: str):
        stmt = (
            delete(Opportunities)
            .where(Opportunities.id == opportunity_id)
            .returning(Opportunities.id)
        )

        is_deleted = (await self.session.execute(stmt)).scalar_one_or_none()

        return is_deleted


    async def get(self, offset: int = 1, limit: int = 10, query: str = ""):
        cursor = (offset - 1) * limit
        search = f"%{query.lower()}%"
        date_expr=func.date(func.timezone("Asia/Kolkata",Opportunities.created_at))

        result = await self.session.execute(
            select(
                *self.oppr_cols,
                date_expr.label("oppotunity_created_at"),

                # Lead fields
                Leads.id.label("lead_id"),
                Leads.name.label("lead_name"),
                Leads.phone.label("lead_phone"),
                Leads.email.label("lead_email"),
                Leads.source.label("lead_source"),
                Leads.assigned_to.label("lead_assigned_to")
            )
            .join(Leads, Leads.id == Opportunities.lead_id)
            .where(
                or_(
                    Opportunities.name.ilike(search),
                    Opportunities.product.ilike(search),
                    Opportunities.status.ilike(search),
                    Opportunities.description.ilike(search),
                    func.cast(Opportunities.created_at,String).ilike(search),
                    
                    Leads.name.ilike(search),
                    Leads.phone.ilike(search),
                    Leads.email.ilike(search),
                    Leads.status.ilike(search),
                    Leads.source.ilike(search),
                    Leads.description.ilike(search)
                ),
                Opportunities.sequence_id > cursor
            )
            .limit(limit)
        )

        opportunities = result.mappings().all()

        total = (
            await self.session.execute(
                select(func.count(Opportunities.id))
            )
        ).scalar_one()

        return {
            "opportunities": opportunities,
            "total_opportunities": total,
            "total_pages": ceil(total / limit)
        }
            


    async def get_by_lead(self, lead_id: str):
        date_expr=func.date(func.timezone("Asia/Kolkata",Opportunities.created_at))
        opp = (
            await self.session.execute(
                select(
                    *self.oppr_cols,
                    date_expr.label("oppotunity_created_at"),

                    # Lead fields
                    Leads.id.label("lead_id"),
                    Leads.name.label("lead_name"),
                    Leads.phone,
                    Leads.email,
                    Leads.source,
                    Leads.assigned_to
                )
                .join(Leads, Leads.id == Opportunities.lead_id)
                .where(Opportunities.lead_id == lead_id)
            )
        ).mappings().all()

        return {"opportunities": opp}
    

    async def search(self, query: str):
        search = f"%{query.lower()}%"

        result = await self.session.execute(
            select(
                *self.oppr_cols,

                # Lead data
                Leads.id.label("lead_id"),
                Leads.name.label("lead_name"),
                Leads.phone,
                Leads.email
            )
            .join(Leads, Leads.id == Opportunities.lead_id)
            .where(
                or_(
                    Opportunities.name.ilike(search),
                    Opportunities.product.ilike(search),
                    Opportunities.status.ilike(search),
                    Opportunities.description.ilike(search),

                    Leads.name.ilike(search),
                    Leads.phone.ilike(search),
                    Leads.email.ilike(search),
                    Leads.status.ilike(search),
                    Leads.source.ilike(search),
                    Leads.description.ilike(search)
                )
            )
            .limit(5)
        )

        opportunities = result.mappings().all()

        return {"opportunities": opportunities}
        

    async def get_by_id(self, opportunity_id:str):
        date_expr=func.date(func.timezone("Asia/Kolkata",Opportunities.created_at))

        result = await self.session.execute(
            select(
                *self.oppr_cols,
                date_expr.label("oppotunity_created_at"),

                # Lead fields
                Leads.id.label("lead_id"),
                Leads.name.label("lead_name"),
                Leads.phone.label("lead_phone"),
                Leads.email.label("lead_email"),
                Leads.source.label("lead_source"),
                Leads.assigned_to.label("lead_assigned_to")
            )
            .join(Leads, Leads.id == Opportunities.lead_id)
            .where(
                Opportunities.id==opportunity_id
            )
        )

        opportunities = result.mappings().one_or_none()

        return {
            "opportunity":opportunities
        }
