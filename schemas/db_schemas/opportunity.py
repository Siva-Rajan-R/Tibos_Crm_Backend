from pydantic import BaseModel
from typing import Optional,Union
from core.data_formats.enums.lead_oppr_enums import OpportunityStatus
from core.data_formats.enums.order_enums import BillingType

class CreateOpportunityDbSchema(BaseModel):
    lui_id:Optional[str]=None
    id:str
    ui_id:str
    lead_id: str
    name: str
    product: str
    billing_type: BillingType
    deal_value: float
    description: Optional[str] = None
    status:str


class UpdateOpportunityDbSchema(BaseModel):
    opportunity_id: str
    name: Optional[str]=None
    product: Optional[str]=None
    billing_type: Optional[BillingType]=None
    deal_value: Optional[float]=None
    description: Optional[str] = None
    status: Optional[str]=None
