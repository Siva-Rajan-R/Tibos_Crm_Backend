from pydantic import BaseModel,EmailStr
from core.data_formats.enums.common_enums import UserRoles
from typing import Optional

class AddUserSchema(BaseModel):
    name:str
    email:EmailStr
    role:UserRoles

class UpdateUserSchema(BaseModel):
    user_id:str
    name:Optional[str]=None
    role:Optional[UserRoles]=None
    
class UserRoleUpdateSchema(BaseModel):
    user_id:str
    role:UserRoles