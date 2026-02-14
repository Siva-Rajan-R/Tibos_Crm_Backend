from pydantic import BaseModel,EmailStr
from typing import Optional,List,Union
from core.data_formats.enums.pg_enums import CustomerIndustries,CustomerSectors
from core.data_formats.typed_dicts.customer_dict import CustomerAddressTypDict

class AddCustomerSchema(BaseModel):
    name:str
    mobile_number:str
    emails:List[EmailStr]
    website_url:Optional[str]=None
    no_of_employee:int
    gst_number:Optional[str]=None
    industry:Union[str,CustomerIndustries]
    sector:Union[str,CustomerSectors]
    address:CustomerAddressTypDict
    owner:str
    tenant_id:str

class UpdateCustomerSchema(BaseModel):
    customer_id:str
    name:Optional[str]=None
    mobile_number:Optional[str]=None
    emails:Optional[List[EmailStr]]=None
    website_url:Optional[str]=None
    no_of_employee:Optional[int]=None
    gst_number:Optional[str]=None
    industry:Optional[Union[str,CustomerIndustries]]=None
    sector:Optional[Union[str,CustomerSectors]]=None
    address:Optional[CustomerAddressTypDict]=None
    owner:Optional[str]=None
    tenant_id:Optional[str]=None

class RecoverCustomerSchema(BaseModel):
    customer_id:str