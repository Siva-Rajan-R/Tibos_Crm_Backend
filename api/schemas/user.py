from pydantic import BaseModel,EmailStr
from data_formats.enums.common_enums import UserRoles


class UserRoleUpdateSchema(BaseModel):
    user_id:str
    role:UserRoles