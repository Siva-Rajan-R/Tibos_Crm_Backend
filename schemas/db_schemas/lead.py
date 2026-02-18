from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import date
from core.data_formats.enums.lead_oppr_enums import LeadSource, LeadStatus


class AddLeadDbSchema(BaseModel):
    lui_id:Optional[str]=None
    id:str
    ui_id:str
    name: str
    email: Optional[EmailStr] = None
    phone: str
    source: LeadSource
    status: LeadStatus
    assigned_to: Optional[str] = None
    last_contacted: Optional[date] = None
    next_followup: Optional[date] = None
    description: Optional[str] = None

    model_config={
        'use_enum_values':True
    }


class UpdateLeadDbSchema(BaseModel):
    lead_id: str
    name: Optional[str]=None
    email: Optional[EmailStr] = None
    phone: Optional[str]=None
    source: Optional[LeadSource]=None
    status: Optional[LeadStatus]=None
    assigned_to: Optional[str] = None
    last_contacted: Optional[date] = None
    next_followup: Optional[date] = None
    description: Optional[str] = None

    model_config={
        'use_enum_values':True
    }
