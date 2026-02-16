from pydantic import BaseModel,EmailStr
from typing import Optional


class SettingsSchema(BaseModel):
    client_secret:str
    tenant_id:str
    client_id:str

class EmailSettingSchema(BaseModel):
    client_secret:str
    tenant_id:str
    client_id:str
    email:EmailStr