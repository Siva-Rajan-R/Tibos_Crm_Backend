from pydantic import BaseModel, EmailStr
from typing import Optional, List


class SettingsSchema(BaseModel):
    client_secret:str
    tenant_id:str
    client_id:str

class EmailSettingSchema(BaseModel):
    client_secret:str
    tenant_id:str
    client_id:str
    email:EmailStr


class DailyScheduleSchema(BaseModel):
    enabled: bool = False
    time: str = "08:00"

class WeeklyScheduleSchema(BaseModel):
    enabled: bool = False
    day: str = "Monday"
    time: str = "08:00"

class MonthlyScheduleSchema(BaseModel):
    enabled: bool = False
    day: int = 1
    time: str = "08:00"

class ScheduleConfigSchema(BaseModel):
    daily: DailyScheduleSchema = DailyScheduleSchema()
    weekly: WeeklyScheduleSchema = WeeklyScheduleSchema()
    monthly: MonthlyScheduleSchema = MonthlyScheduleSchema()

class ReportScheduleSchema(BaseModel):
    schedule: ScheduleConfigSchema


class PendingDuesAlertSchema(BaseModel):
    enabled: bool = False
    time: str = "09:00"
    recipients: List[EmailStr] = []
    categories: List[str] = []

class EmailUpdateSchema(BaseModel):
    email: EmailStr
    tenant_id: str
    client_id: str
    client_secret: Optional[str] = None

class PendingDuesAlertTestSchema(BaseModel):
    recipients: List[EmailStr]
    categories: List[str]