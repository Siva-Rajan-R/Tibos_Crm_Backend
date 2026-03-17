from pydantic import BaseModel,EmailStr
from typing import Optional,List,Union
from core.data_formats.enums.customer_enums import CustomerIndustries,CustomerSectors
from core.data_formats.typed_dicts.customer_typdict import CustomerAddressTypDict

class AddCustomerSchema(BaseModel):
    name:str
    mobile_number:str
    emails:List[EmailStr]
    website_url:Optional[str]=None
    no_of_employee:int
    gst_number:Optional[str]=None
    industry:str
    sector:str
    address:CustomerAddressTypDict
    owner:str
    tenant_id:str
    secondary_domain:Optional[str]=None
    is_active:bool

class UpdateCustomerSchema(BaseModel):
    customer_id:str
    name:Optional[str]=None
    mobile_number:Optional[str]=None
    emails:Optional[List[EmailStr]]=None
    website_url:Optional[str]=None
    no_of_employee:Optional[int]=None
    gst_number:Optional[str]=None
    industry:Optional[str]=None
    sector:Optional[str]=None
    address:Optional[CustomerAddressTypDict]=None
    owner:Optional[str]=None
    tenant_id:Optional[str]=None
    secondary_domain:Optional[str]=None
    is_active:Optional[bool]=None

class AddSearchFields(BaseModel):
    ui_id:str
    id:str
    name:str
    mobile_number:str
    email:str
    tenant_id:str
    secondary_domain:Optional[str]=None
    sector:str
    industry:str

class UpdateSearchFields(BaseModel):
    name:Optional[str]=None
    mobile_number:Optional[str]=None
    email:Optional[str]=None
    tenant_id:Optional[str]=None
    secondary_domain:Optional[str]=None
    sector:Optional[str]=None
    industry:Optional[str]=None


class RecoverCustomerSchema(BaseModel):
    customer_id:str

class ResponseSearch(BaseModel):
    id:str
    name:str

class FinalResponseModel(BaseModel):
    customers:List[ResponseSearch]