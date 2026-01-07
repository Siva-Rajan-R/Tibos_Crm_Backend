from pydantic import BaseModel,EmailStr
from core.data_formats.enums.common_enums import UserRoles
from typing import Optional

class AddUserDbSchema(BaseModel):
    id:str
    name:str
    email:EmailStr
    role:UserRoles
    password:str

class UpdateUserDbSchema(BaseModel):
    user_id:str
    name:Optional[str]=None
    role:Optional[UserRoles]=None
    
class UserRoleUpdateSchema(BaseModel):
    user_id:str
    role:UserRoles