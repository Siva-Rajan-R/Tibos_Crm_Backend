from pydantic import BaseModel,EmailStr
from typing import Optional,List


class AddContactDbSchema(BaseModel):
    id:str
    name:str
    customer_id:str
    mobile_number:str
    email:EmailStr



class UpdateContactDbSchema(BaseModel):
    contact_id:str
    customer_id:str
    name:Optional[str]=None
    mobile_number:Optional[str]=None
    email:Optional[EmailStr]=None