from pydantic import BaseModel,EmailStr
from data_formats.enums.common_enums import UserRoles

class AddUserSchema(BaseModel):
    name:str
    email:EmailStr
    role:UserRoles

class UpdateUserSchema(BaseModel):
    user_id:str
    name:str
    role:UserRoles
    
class UserRoleUpdateSchema(BaseModel):
    user_id:str
    role:UserRoles