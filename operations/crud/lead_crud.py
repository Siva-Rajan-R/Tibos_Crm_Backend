from globals.fastapi_globals import HTTPException
from database.models.pg_models.leads import Leads
from utils.uuid_generator import generate_uuid
from sqlalchemy import select, delete, update, or_, func,String
from sqlalchemy.ext.asyncio import AsyncSession
from icecream import ic
from data_formats.enums.common_enums import UserRoles
from data_formats.enums.pg_enums import OpportunityStatus,LeadSource,LeadStatus
from database.models.pg_models.leads import Leads
from math import ceil
from datetime import datetime
from typing import Optional
from operations.abstract_models.crud_model import BaseCrud


class LeadsCrud(BaseCrud):
    def __init__(self, session: AsyncSession, user_role: UserRoles):
        self.session = session
        self.user_role = user_role

        if self.user_role == UserRoles.USER.value:
            raise HTTPException(status_code=401, detail="Not a valid user")

    async def add(
        self,
        name: str,
        email: Optional[str],
        phone: str,
        source:LeadSource,
        assigned_to: Optional[str],
        description: Optional[str],
        status: LeadStatus,
        last_contacted: Optional[datetime] = None,
        next_followup: Optional[datetime] = None
    ):
        try:
            async with self.session.begin():
                lead = Leads(
                    id=generate_uuid(data=name),
                    name=name,
                    email=email,
                    phone=phone,
                    source=source.value,
                    status=status.value,
                    assigned_to=assigned_to,
                    description=description,
                    last_contacted=last_contacted,
                    next_followup=next_followup
                )

                self.session.add(lead)
                return "Lead created successfully"
        except HTTPException:
            raise
        except Exception as e:
            ic(e)
            raise HTTPException(500, f"Failed to create lead: {e}")

    async def update(
        self,
        lead_id: str,
        name: str,
        email: Optional[str],
        phone: str,
        source:LeadSource,
        status: LeadStatus,
        last_contacted: datetime,
        next_followup:datetime,
        description: Optional[str]=None,
        assigned_to: Optional[str]=None,
    ):
        try:
            async with self.session.begin():
                stmt = (
                    update(Leads)
                    .where(Leads.id == lead_id)
                    .values(
                        name=name,
                        email=email,
                        phone=phone,
                        source=source.value,
                        status=status.value,
                        assigned_to=assigned_to,
                        last_contacted=last_contacted,
                        next_followup=next_followup,
                        description=description
                    )
                    .returning(Leads.id)
                )

                updated_id = (await self.session.execute(stmt)).scalar_one_or_none()

                if not updated_id:
                    raise HTTPException(404, "Invalid Lead ID")

                return "Lead updated successfully"

        except HTTPException:
            raise
        except Exception as e:
            ic(e)
            raise HTTPException(500, f"Failed to update lead: {e}")

    async def delete(self, lead_id: str):
        try:
            async with self.session.begin():
                stmt = delete(Leads).where(Leads.id == lead_id).returning(Leads.id)
                deleted_id = (await self.session.execute(stmt)).scalar_one_or_none()

                if not deleted_id:
                    raise HTTPException(404, "Invalid Lead ID")

                return "Lead deleted successfully"
        except HTTPException:
            raise
        except Exception as e:
            ic(e)
            raise HTTPException(500, f"Failed to delete lead: {e}")

    async def get(self, offset: int = 1, limit: int = 10, query: str = ""):
        try:
            cursor = (offset - 1) * limit
            search = f"%{query.lower()}%"
            date_expr=func.date(func.timezone("Asia/Kolkata",Leads.created_at))
            follwup_expr=func.date(func.timezone("Asia/Kolkata",Leads.next_followup))
            lastcont_expr=func.date(func.timezone("Asia/Kolkata",Leads.last_contacted))

            leads = (
                await self.session.execute(
                    select(
                        Leads.id.label("lead_id"),
                        Leads.name.label("lead_name"), 
                        Leads.description.label("lead_description"),
                        Leads.phone.label("lead_phone"),
                        Leads.email.label("lead_email"),
                        Leads.source.label("lead_source"),
                        Leads.assigned_to.label("lead_assigned_to"),
                        Leads.status.label("lead_status"),
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
        
        except HTTPException:
            raise

        except Exception as e:
            ic(e)
            raise HTTPException(500, f"Failed to fetch leads: {e}")

    async def get_by_id(self, lead_id: str):
        date_expr=func.date(func.timezone("Asia/Kolkata",Leads.created_at))
        follwup_expr=func.date(func.timezone("Asia/Kolkata",Leads.next_followup))
        lastcont_expr=func.date(func.timezone("Asia/Kolkata",Leads.last_contacted))
        lead = (
            await self.session.execute(
                select( 
                    Leads.id.label("lead_id"),
                    Leads.name.label("lead_name"),
                    Leads.description.label("lead_description"),
                    Leads.phone.label("lead_phone"),
                    Leads.email.label("lead_email"),
                    Leads.source.label("lead_source"),
                    Leads.assigned_to.label("lead_assigned_to"),
                    Leads.status.label("lead_status"),
                    follwup_expr.label("lead_next_followup"),
                    lastcont_expr.label("lead_last_contacted"),
                    date_expr.label("lead_created_at")
                ).where(Leads.id == lead_id)
            )
        ).mappings().one_or_none()

        if not lead:
            raise HTTPException(404, "Lead not found")

        return {"lead": lead}
    

    async def search(self, query: str):
        try:
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
        except HTTPException:
            raise
        except Exception as e:
            ic(e)
            raise HTTPException(
                status_code=500,
                detail=f"Failed to search leads: {e}"
            )
