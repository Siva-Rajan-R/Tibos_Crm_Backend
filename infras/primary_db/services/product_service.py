from . import BaseServiceModel
from ..models.product import Products,ProductTypes
from ..models.order import Orders
from core.utils.uuid_generator import generate_uuid
from sqlalchemy import select,delete,update,or_,cast,String,func,Float
from sqlalchemy.ext.asyncio import AsyncSession
from icecream import ic
from core.data_formats.enums.common_enums import UserRoles
from core.decorators.error_handler_dec import catch_errors
from ..repos.product_repo import ProductsRepo
from schemas.db_schemas.product import AddProductDbSchema,UpdateProductDbSchema
from schemas.request_schemas.product import AddProductSchema,UpdateProductSchema
from math import ceil



class ProductsService(BaseServiceModel):
    def __init__(self,session:AsyncSession,user_role:UserRoles):
        self.session=session
        self.user_role=user_role
        
    @catch_errors
    async def add(self,data:AddProductSchema):
        prod_id:str=generate_uuid()
        return await ProductsRepo(session=self.session,user_role=self.user_role).add(data=AddProductDbSchema(**data.model_dump(mode='json'),id=prod_id))


    @catch_errors   
    async def update(self,data:UpdateProductDbSchema):
        data_toupdate=data.model_dump(mode='json',exclude_none=True,exclude_unset=True)
        if not data_toupdate or len(data_toupdate)<1:
            return False
        return await ProductsRepo(session=self.session,user_role=self.user_role).update(data=UpdateProductDbSchema(**data_toupdate))

    @catch_errors
    async def recover(self,product_torecover:str):
        return await ProductsRepo(session=self.session,user_role=self.user_role).recover(product_torecover=product_torecover)

    @catch_errors
    async def delete(self,product_id:str,soft_delete:bool=True):
        return await ProductsRepo(session=self.session,user_role=self.user_role).delete(product_id=product_id,soft_delete=soft_delete)

    @catch_errors   
    async def get(self,offset:int=1,limit:int=10,query:str=''):
        return await ProductsRepo(session=self.session,user_role=self.user_role).get(offset=offset,limit=limit,query=query)
    
    @catch_errors
    async def search(self, query: str):
        return await ProductsRepo(session=self.session,user_role=self.user_role).search(query=query)
    
    @catch_errors
    async def get_by_id(self,product_id:str):
        return await ProductsRepo(session=self.session,user_role=self.user_role).get_by_id(product_id=product_id)



