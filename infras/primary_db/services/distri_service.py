from . import BaseServiceModel
from ..repos.product_repo import ProductsRepo
from ..models.distributor import Distributors
from ..repos.distri_repo import DistributorsRepo
from ..repos.order_repo import OrdersRepo
from core.utils.uuid_generator import generate_uuid
from ..models.order import Orders
from sqlalchemy import select,delete,update,or_,func,String
from sqlalchemy.ext.asyncio import AsyncSession
from icecream import ic
from core.data_formats.enums.common_enums import UserRoles
from pydantic import EmailStr
from typing import Optional,List
from schemas.db_schemas.distributor import CreateDistriDbSchema,UpdateDistriDbSchema
from schemas.request_schemas.distributor import CreateDistriSchema,UpdateDistriSchema
from core.decorators.error_handler_dec import catch_errors
from math import ceil



class DistributorService(BaseServiceModel):
    def __init__(self,session:AsyncSession,user_role:UserRoles):
        self.session=session
        self.user_role=user_role

       
    @catch_errors
    async def add(self,data:CreateDistriSchema):
        if not (await ProductsRepo(session=self.session,user_role=self.user_role).get_by_id(product_id=data.product_id)):
            return False
        
        distri_id:str=generate_uuid()
        return await DistributorsRepo(session=self.session,user_role=self.user_role).add(data=CreateDistriDbSchema(**data.model_dump(mode='json'),id=distri_id))
        
    @catch_errors  
    async def update(self,data:UpdateDistriSchema):
        data_toupdate=data.model_dump(mode='json',exclude_none=True,exclude_unset=True)

        if not data_toupdate or len(data_toupdate)<1:
            return False
        
        if data.product_id and not (await ProductsRepo(session=self.session,user_role=self.user_role).get_by_id(product_id=data.product_id)):
            return False
        
        return await DistributorsRepo(session=self.session,user_role=self.user_role).update(data=UpdateDistriDbSchema(**data_toupdate))
        
    @catch_errors
    async def delete(self,distributor_id:str):
        if await OrdersRepo(session=self.session,user_role=self.user_role).get(query=distributor_id,limit=1):
            return False
        
        return await DistributorsRepo(session=self.session,user_role=self.user_role).delete(distri_id=distributor_id)
        
    @catch_errors
    async def get(self,offset:int=1,limit:int=10,query:str=''):
        return await DistributorsRepo(session=self.session,user_role=self.user_role).get(offset=offset,limit=limit,query=query)
        
    @catch_errors
    async def search(self,query:str):
        return await DistributorsRepo(session=self.session,user_role=self.user_role).search(query=query)

    @catch_errors
    async def get_by_id(self,distributor_id:str):
        return await DistributorsRepo(session=self.session,user_role=self.user_role).get_by_id(distributor_id=distributor_id)



