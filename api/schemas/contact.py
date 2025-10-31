from pydantic import BaseModel,EmailStr


class AddContactSchema(BaseModel):
    name:str
    customer_id:str
    mobile_number:str
    email:EmailStr



class UpdateContactSchema(BaseModel):
    contact_id:str
    name:str
    customer_id:str
    mobile_number:str
    email:EmailStr