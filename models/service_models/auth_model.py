from abc import ABC,abstractmethod


class AuthModel(ABC):
    @abstractmethod
    async def get_login_link(self):
        ...
    
    @abstractmethod
    async def get_authenticated_user(self,*args,**kwargs):
        ...