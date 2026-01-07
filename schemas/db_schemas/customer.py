from pydantic import BaseModel,EmailStr
from typing import Optional,List
from core.data_formats.enums.pg_enums import CustomerIndustries,CustomerSectors

class AddCustomerDbSchema(BaseModel):
    id:str
    name:str
    mobile_number:str
    email:EmailStr
    website_url:Optional[str]
    no_of_employee:int
    gst_number:Optional[str]
    industry:CustomerIndustries
    sector:CustomerSectors
    address:str

class UpdateCustomerDbSchema(BaseModel):
    customer_id:str
    name:Optional[str]=None
    mobile_number:Optional[str]=None
    email:Optional[EmailStr]=None
    website_url:Optional[str]=None
    no_of_employee:Optional[int]=None
    gst_number:Optional[str]=None
    industry:Optional[CustomerIndustries]=None
    sector:Optional[CustomerSectors]=None
    address:Optional[str]=None