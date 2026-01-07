from abc import ABC,abstractmethod
from pydantic import EmailStr

class BaseServiceModel(ABC):
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
    
    @abstractmethod
    async def search(self,*args,**kwargs):
        ...