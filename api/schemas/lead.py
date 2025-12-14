from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from data_formats.enums.pg_enums import LeadSource, LeadStatus


class AddLeadSchema(BaseModel):
    name: str
    email: Optional[EmailStr] = None
    phone: str
    source: LeadSource
    status: LeadStatus
    assigned_to: Optional[str] = None
    last_contacted: Optional[datetime] = None
    next_followup: Optional[datetime] = None
    description: Optional[str] = None


class UpdateLeadSchema(BaseModel):
    lead_id: str
    name: str
    email: Optional[EmailStr] = None
    phone: str
    source: LeadSource
    status: LeadStatus
    assigned_to: Optional[str] = None
    last_contacted: Optional[datetime] = None
    next_followup: Optional[datetime] = None
    description: Optional[str] = None
