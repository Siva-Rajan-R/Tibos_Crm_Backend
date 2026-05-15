from pydantic import BaseModel, EmailStr
from typing import Any, Dict, Optional, List


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
    recipients: List[EmailStr] = []


class PendingDuesAlertSchema(BaseModel):
    enabled: bool = False
    time: str = "09:00"
    recipients: List[EmailStr] = []
    categories: List[str] = []
    counts: Optional[Dict[str, Any]] = None
    email_template_html: Optional[str] = None

class EmailUpdateSchema(BaseModel):
    email: EmailStr
    tenant_id: str
    client_id: str
    client_secret: Optional[str] = None

class PendingDuesAlertTestSchema(BaseModel):
    recipients: List[EmailStr]
    categories: List[str]
    counts: Optional[Dict[str, Any]] = None
    html: Optional[str] = None

class EmailTemplateSchema(BaseModel):
    template_config: Dict[str, Any]


class PendingInvoiceAlertSchema(BaseModel):
    enabled: bool = False
    days_after_order_created: int = 1


class ActivationDateAlertSchema(BaseModel):
    enabled: bool = False
    days_before_activation: int = 2
    days_after_activation: int = 2


class TriggerTestReportSchema(BaseModel):
    report_type: str
    recipients: List[EmailStr]


class GlobalAlertsSchema(BaseModel):
    recipients: List[EmailStr] = []
    sender_email: Optional[EmailStr] = None
    
    # Reports Schedule (Payment Summary + Pending)
    payment_summary_enabled: bool = True
    payment_pending_enabled: bool = True
    payment_pending_min_days: Optional[int] = None
    daily: DailyScheduleSchema = DailyScheduleSchema()
    weekly: WeeklyScheduleSchema = WeeklyScheduleSchema()
    monthly: MonthlyScheduleSchema = MonthlyScheduleSchema()
    
    # Pending Dues Alert
    dues_enabled: bool = False
    dues_time: str = "09:00"
    dues_categories: List[str] = []
    
    # Pending Invoice Alert
    invoice_enabled: bool = False
    invoice_time: str = "09:00"
    invoice_days: int = 1
    
    # Activation Date Alert
    activation_enabled: bool = False
    activation_time: str = "09:00"
    activation_before: int = 2
    activation_after: int = 2