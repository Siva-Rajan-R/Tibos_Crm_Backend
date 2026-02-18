from pydantic import BaseModel,EmailStr
from typing import Optional,List,Union
from core.data_formats.enums.customer_enums import CustomerIndustries,CustomerSectors
from core.data_formats.typed_dicts.customer_typdict import CustomerAddressTypDict

class AddCustomerDbSchema(BaseModel):
    lui_id:Optional[str]=None
    id:str
    ui_id:str
    name:str
    mobile_number:str
    email:str
    website_url:Optional[str]
    no_of_employee:int
    gst_number:Optional[str]
    industry:str
    sector:str
    address:CustomerAddressTypDict
    owner:str
    tenant_id:str

class UpdateCustomerDbSchema(BaseModel):
    customer_id:str
    name:Optional[str]=None
    mobile_number:Optional[str]=None
    email:str
    website_url:Optional[str]=None
    no_of_employee:Optional[int]=None
    gst_number:Optional[str]=None
    industry:Optional[str]=None
    sector:Optional[str]=None
    address:Optional[CustomerAddressTypDict]=None
    owner:Optional[str]=None
    tenant_id:Optional[str]=None