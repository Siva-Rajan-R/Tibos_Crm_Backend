from pydantic import BaseModel,EmailStr
from core.data_formats.enums.common_enums import UserRoles
from typing import Optional

class AddUserDbSchema(BaseModel):
    lui_id:Optional[str]=None
    id:str
    ui_id:str
    name:str
    email:EmailStr
    role:UserRoles
    password:str
    token_version:Optional[float]=0.0

class UpdateUserDbSchema(BaseModel):
    user_id:str
    name:Optional[str]=None
    role:Optional[UserRoles]=None
    
class UserRoleUpdateSchema(BaseModel):
    user_id:str
    role:UserRoles