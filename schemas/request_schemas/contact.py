from pydantic import BaseModel,EmailStr
from typing import Optional


class AddContactSchema(BaseModel):
    name:str
    customer_id:str
    mobile_number:str
    email:EmailStr

class AddSearchField(BaseModel):
    ui_id:str
    id:str
    name:str
    email:str
    mobile_number:str
    customer_id:str


class UpdateSearchField(BaseModel):
    name:Optional[str]=None
    email:Optional[str]=None
    mobile_number:Optional[str]=None
    customer_id:Optional[str]=None

class UpdateContactSchema(BaseModel):
    contact_id:str
    name:Optional[str]=None
    customer_id:str
    mobile_number:Optional[str]=None
    email:Optional[EmailStr]=None

class RecoverContactSchema(BaseModel):
    contact_id:str
    customer_id:str