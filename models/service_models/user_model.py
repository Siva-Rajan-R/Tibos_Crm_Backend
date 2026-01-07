from abc import ABC,abstractmethod
from core.data_formats.enums.common_enums import UserRoles
from pydantic import EmailStr
from .base_model import BaseServiceModel


class UserServiceModel(BaseServiceModel):
    @abstractmethod
    async def get_by_role(self,userrole_toget:UserRoles,*args,**kwargs):
        ...
    
    @abstractmethod
    async def isuser_exists(self,user_id_email:str,*args,**kwargs):
        ...
    
    @abstractmethod
    async def update_role(self,email_toupdate:EmailStr,role_toupdate:UserRoles,*args,**kwargs):
        ...
    
    @abstractmethod
    async def init_superadmin(self):
        ...