from abc import ABC,abstractmethod
from data_formats.enums.common_enums import UserRoles
from pydantic import EmailStr

class BaseCrud(ABC):
    @abstractmethod
    async def add(self,*args,**kwargs):
        ...
    
    @abstractmethod
    async def update(self,*args,**kwargs):
        ...
    
    @abstractmethod
    async def delete(self,*args,**kwargs):
        ...
    
    @abstractmethod
    async def get(self,*args,**kwargs):
        ...
    
    @abstractmethod
    async def get_by_id(self,*args,**kwargs):
        ...


class UserCrudModel(BaseCrud):
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


