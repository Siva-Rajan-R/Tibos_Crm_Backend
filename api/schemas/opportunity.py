from pydantic import BaseModel
from typing import Optional
from data_formats.enums.pg_enums import OpportunityStatus, BillingType


class CreateOpportunitySchema(BaseModel):
    lead_id: str
    name: str
    product: str
    billing_type: BillingType
    deal_value: float
    description: Optional[str] = None
    status:OpportunityStatus


class UpdateOpportunitySchema(BaseModel):
    opportunity_id: str
    name: str
    product: str
    billing_type: BillingType
    deal_value: float
    description: Optional[str] = None
    status: OpportunityStatus
