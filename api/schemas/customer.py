from pydantic import BaseModel,EmailStr
from typing import Optional,List
from data_formats.enums.pg_enums import CustomerIndustries,CustomerSectors

class AddCustomerSchema(BaseModel):
    name:str
    mobile_number:str
    email:EmailStr
    website_url:Optional[str]
    no_of_employee:int
    gst_number:Optional[str]
    industry:CustomerIndustries
    sector:CustomerSectors
    address:str

class UpdateCustomerSchema(BaseModel):
    customer_id:str
    name:str
    mobile_number:str
    email:EmailStr
    website_url:Optional[str]
    no_of_employee:int
    gst_number:Optional[str]
    industry:CustomerIndustries
    sector:CustomerSectors
    address:str