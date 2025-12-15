from globals.fastapi_globals import HTTPException
from database.models.pg_models.opportunity import Opportunities
from database.models.pg_models.leads import Leads
from sqlalchemy import select, delete, update,func,or_,String
from sqlalchemy.ext.asyncio import AsyncSession
from icecream import ic
from data_formats.enums.common_enums import UserRoles
from typing import Optional
from data_formats.enums.pg_enums import OpportunityStatus,LeadSource,LeadStatus,BillingType
from operations.abstract_models.crud_model import BaseCrud
from utils.uuid_generator import generate_uuid
from datetime import datetime
from math import ceil


class OpportunitiesCrud(BaseCrud):
    def __init__(self, session: AsyncSession, user_role: UserRoles):
        self.session = session
        self.user_role = user_role

        if self.user_role == UserRoles.USER.value:
            raise HTTPException(status_code=401, detail="Not a valid user")

    async def add(
        self,
        lead_id: str,
        name: str,
        product: str,
        status:OpportunityStatus,
        billing_type:BillingType,
        deal_value: float,
        description: Optional[str]
    ):
        try:
            async with self.session.begin():
                oppr_id:str=generate_uuid(name)
                opp = Opportunities(
                    id=oppr_id,
                    lead_id=lead_id,
                    name=name,
                    product=product,
                    billing_type=billing_type.value,
                    status=status.value,  # or initial state
                    deal_value=deal_value,
                    description=description
                )

                self.session.add(opp)
                return "Opportunity created successfully"

        except Exception as e:
            ic(e)
            raise HTTPException(500, f"Failed to create opportunity: {e}")

    async def update(
        self,
        opportunity_id: str,
        name: str,
        product: str,
        billing_type:BillingType,
        deal_value: float,
        description: Optional[str],
        status: OpportunityStatus,
    ):
        try:
            async with self.session.begin():
                stmt = (
                    update(Opportunities)
                    .where(Opportunities.id == opportunity_id)
                    .values(
                        name=name,
                        billing_type=billing_type.value,
                        product=product,
                        status=status.value,
                        deal_value=deal_value,
                        description=description
                    )
                    .returning(Opportunities.id)
                )

                updated_id = (await self.session.execute(stmt)).scalar_one_or_none()

                if not updated_id:
                    raise HTTPException(404, "Invalid Opportunity ID")

                return "Opportunity updated successfully"
        except HTTPException:
            raise
        except Exception as e:
            ic(e)
            raise HTTPException(500, f"Failed to update opportunity: {e}")

    async def delete(self, opportunity_id: str):
        try:
            async with self.session.begin():
                stmt = (
                    delete(Opportunities)
                    .where(Opportunities.id == opportunity_id)
                    .returning(Opportunities.id)
                )

                deleted_id = (await self.session.execute(stmt)).scalar_one_or_none()

                if not deleted_id:
                    raise HTTPException(404, "Invalid Opportunity ID")

                return "Opportunity deleted successfully"
        except HTTPException:
            raise
        except Exception as e:
            ic(e)
            raise HTTPException(500, f"Failed to delete opportunity: {e}")

    async def get(self, offset: int = 1, limit: int = 10, query: str = ""):
        try:
            cursor = (offset - 1) * limit
            search = f"%{query.lower()}%"
            date_expr=func.date(func.timezone("Asia/Kolkata",Opportunities.created_at))

            result = await self.session.execute(
                select(
                    Opportunities.id.label("opportunity_id"),
                    Opportunities.name.label("opportunity_name"),
                    Opportunities.product.label("opportunity_product"),
                    Opportunities.status.label("opportunity_status"),
                    Opportunities.deal_value.label("opportunity_deal_value"),
                    Opportunities.billing_type.label("opportunity_billing_type"),
                    Opportunities.description.label("opportunity_description"),
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
        except HTTPException:
            raise
        except Exception as e:
            ic(e)
            raise HTTPException(
                status_code=500,
                detail=f"Failed to fetch opportunities: {e}"
            )
            
    async def get_by_lead(self, lead_id: str):
        date_expr=func.date(func.timezone("Asia/Kolkata",Opportunities.created_at))
        opp = (
            await self.session.execute(
                select(
                    Opportunities.id.label("opportunity_id"),
                    Opportunities.name.label("opportunity_name"),
                    Opportunities.product.label("opportunity_product"),
                    Opportunities.status.label("opportunity_status"),
                    Opportunities.deal_value.label("opportunity_deal_value"),
                    Opportunities.billing_type.label("opportunity_billing_type"),
                    Opportunities.description.label("opportunity_description"),
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
        try:
            search = f"%{query.lower()}%"

            result = await self.session.execute(
                select(
                    Opportunities.id.label("opportunity_id"),
                    Opportunities.name.label("opportunity_name"),
                    Opportunities.product.label("opportunity_product"),
                    Opportunities.status.label("opportunity_status"),
                    Opportunities.deal_value.label("opportunity_deal_value"),
                    Opportunities.billing_type.label("opportunity_billing_type"),
                    Opportunities.description.label("opportunity_description"),

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
        except HTTPException:
            raise
        except Exception as e:
            ic(e)
            raise HTTPException(
                status_code=500,
                detail=f"Failed to search opportunities: {e}"
            )
        
    async def get_by_id(self, opportunity_id:str):
        try:
            date_expr=func.date(func.timezone("Asia/Kolkata",Opportunities.created_at))

            result = await self.session.execute(
                select(
                    Opportunities.id.label("opportunity_id"),
                    Opportunities.name.label("opportunity_name"),
                    Opportunities.product.label("opportunity_product"),
                    Opportunities.status.label("opportunity_status"),
                    Opportunities.deal_value.label("opportunity_deal_value"),
                    Opportunities.billing_type.label("opportunity_billing_type"),
                    Opportunities.description.label("opportunity_description"),
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
        except HTTPException:
            raise
        except Exception as e:
            ic(e)
            raise HTTPException(
                status_code=500,
                detail=f"Failed to fetch opportunity: {e}"
            )
