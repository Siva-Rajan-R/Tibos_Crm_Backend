from pydantic import BaseModel,EmailStr
from data_formats.enums.common_enums import UserRoles


class UserRoleUpdateSchema(BaseModel):
    email:EmailStr
    role:UserRoles