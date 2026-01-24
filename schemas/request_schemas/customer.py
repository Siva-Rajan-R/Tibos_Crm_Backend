from pydantic import BaseModel,EmailStr
from typing import Optional,List
from core.data_formats.enums.pg_enums import CustomerIndustries,CustomerSectors
from core.data_formats.typed_dicts.customer_dict import CustomerAddressTypDict

class AddCustomerSchema(BaseModel):
    name:str
    mobile_number:str
    email:EmailStr
    website_url:Optional[str]=None
    no_of_employee:int
    gst_number:Optional[str]=None
    industry:CustomerIndustries
    sector:CustomerSectors
    address:CustomerAddressTypDict
    owner:str
    tenant_id:str

class UpdateCustomerSchema(BaseModel):
    customer_id:str
    name:Optional[str]=None
    mobile_number:Optional[str]=None
    email:Optional[EmailStr]=None
    website_url:Optional[str]=None
    no_of_employee:Optional[int]=None
    gst_number:Optional[str]=None
    industry:Optional[CustomerIndustries]=None
    sector:Optional[CustomerSectors]=None
    address:Optional[CustomerAddressTypDict]=None
    owner:Optional[str]=None
    tenant_id:Optional[str]=None

class RecoverCustomerSchema(BaseModel):
    customer_id:str