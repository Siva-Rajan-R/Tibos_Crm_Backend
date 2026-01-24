from pydantic import BaseModel,EmailStr
from typing import Optional


class AddContactSchema(BaseModel):
    name:str
    customer_id:str
    mobile_number:str
    email:EmailStr



class UpdateContactSchema(BaseModel):
    contact_id:str
    name:Optional[str]=None
    customer_id:str
    mobile_number:Optional[str]=None
    email:Optional[EmailStr]=None

class RecoverContactSchema(BaseModel):
    contact_id:str
    customer_id:str