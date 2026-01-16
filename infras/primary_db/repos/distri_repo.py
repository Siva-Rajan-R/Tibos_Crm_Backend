from . import HTTPException,BaseRepoModel
from ..models.distributor import Distributors
from ..models.product import Products,ProductTypes
from core.utils.uuid_generator import generate_uuid
from sqlalchemy import select,delete,update,or_,func,String
from sqlalchemy.ext.asyncio import AsyncSession
from icecream import ic
from pydantic import EmailStr
from typing import Optional,List
from core.data_formats.enums.common_enums import UserRoles
from schemas.db_schemas.distributor import CreateDistriDbSchema,UpdateDistriDbSchema
from core.decorators.db_session_handler_dec import start_db_transaction
from math import ceil



class DistributorsRepo(BaseRepoModel):
    def __init__(self,session:AsyncSession,user_role:UserRoles):
        self.session=session
        self.user_role=user_role
        self.distri_cols=(
            Distributors.id,
            Distributors.name,
            Distributors.discount,
            Products.id.label('product_id'),
            Products.name.label('product_name')
        )

        
    @start_db_transaction
    async def add(self,data:CreateDistriDbSchema):
        self.session.add(Distributors(**data.model_dump(mode='json')))
        return True
        
    @start_db_transaction  
    async def update(self,data:UpdateDistriDbSchema):
        data_toupdate=data.model_dump(mode='json',exclude=['id'],exclude_none=True,exclude_unset=True)

        if not data_toupdate or len(data_toupdate)<1:
            return False
        
        distributor_toupdate=update(Distributors).where(Distributors.id==data.id).values(
            **data_toupdate
        ).returning(Distributors.id)

        is_updated=(await self.session.execute(distributor_toupdate)).scalar_one_or_none()
        
        return is_updated
    

    @start_db_transaction
    async def delete(self,distri_id:str):
        distributor_todelete=delete(Distributors).where(Distributors.id==distri_id).returning(Distributors.id)
        is_deleted=(await self.session.execute(distributor_todelete)).scalar_one_or_none()
        
        return is_deleted
        

    async def get(self,offset:int=1,limit:int=10,query:str=''):
        search_term=f"%{query.lower()}%"
        cursor=(offset-1)*limit
        date_expr=func.date(func.timezone("Asia/Kolkata",Distributors.created_at))
        queried_distri=(await self.session.execute(
            select(
                *self.distri_cols,
                date_expr.label("created_at")
            ).limit(limit)
            .join(Products,Products.id==Distributors.product_id)
            .where(
                or_(
                    Distributors.id.ilike(search_term),
                    Distributors.name.ilike(search_term),
                    Distributors.product_id.ilike(search_term),
                    Products.name.ilike(search_term),
                    Products.description.like(search_term),
                    func.cast(Distributors.created_at,String).ilike(search_term),

                ),
                Distributors.sequence_id>cursor
            )
        )).mappings().all()

        total_distributors:int=0
        if offset==1:
            total_distributors=(await self.session.execute(
                select(func.count(Distributors.id))
            )).scalar_one_or_none()

        return {
            'distributors':queried_distri,
            'total_distributors':total_distributors,
            'total_pages':ceil(total_distributors/limit)
        }
        
    
    async def search(self,query:str):
        search_term=f"%{query.lower()}%"
        queried_distributors=(await self.session.execute(
            select(
                Distributors.id,
                Distributors.name,
                Distributors.discount
            ).join(
                Products,Products.id==Distributors.product_id
            ).where(
                or_(
                    Distributors.id.ilike(search_term),
                    Distributors.name.ilike(search_term),
                    Distributors.product_id.ilike(search_term),
                    Products.name.ilike(search_term),
                    Products.description.like(search_term),
                    func.cast(Distributors.created_at,String).ilike(search_term)
                )
            )
            .limit(5)
        )).mappings().all()

        return {'distributors':queried_distributors}

       
    async def get_by_id(self,distributor_id:str):
        date_expr=func.date(func.timezone("Asia/Kolkata",Distributors.created_at))
        queried_distributors=(await self.session.execute(
            select(
                *self.distri_cols,
                date_expr.label("created_at")
            )
            .join(Products,Products.id==Distributors.product_id)
            .where(Distributors.id==distributor_id)
        )).mappings().one_or_none()
        
        return {'distributors':queried_distributors}



