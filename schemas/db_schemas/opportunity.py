from pydantic import BaseModel
from typing import Optional
from core.data_formats.enums.pg_enums import OpportunityStatus, BillingType


class CreateOpportunityDbSchema(BaseModel):
    id:str
    lead_id: str
    name: str
    product: str
    billing_type: BillingType
    deal_value: float
    description: Optional[str] = None
    status:OpportunityStatus


class UpdateOpportunityDbSchema(BaseModel):
    opportunity_id: str
    name: Optional[str]=None
    product: Optional[str]=None
    billing_type: Optional[BillingType]=None
    deal_value: Optional[float]=None
    description: Optional[str] = None
    status: Optional[OpportunityStatus]=None
