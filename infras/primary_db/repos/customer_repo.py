from . import HTTPException,BaseRepoModel
from ..models.customer import Customers,CustomerIndustries,CustomerSectors
from core.utils.uuid_generator import generate_uuid
from ..models.order import Orders
from sqlalchemy import select,delete,update,or_,func,String
from sqlalchemy.ext.asyncio import AsyncSession
from icecream import ic
from core.data_formats.enums.common_enums import UserRoles
from pydantic import EmailStr
from typing import Optional,List
from schemas.db_schemas.customer import AddCustomerDbSchema,UpdateCustomerDbSchema
from core.decorators.db_session_handler_dec import start_db_transaction
from math import ceil



class CustomersRepo(BaseRepoModel):
    def __init__(self,session:AsyncSession,user_role:UserRoles):
        self.session=session
        self.user_role=user_role
        self.customer_cols=(
            Customers.id,
            Customers.name,
            Customers.mobile_number,
            Customers.email,
            Customers.gst_number,
            Customers.no_of_employee,
            Customers.website_url,
            Customers.industry,
            Customers.sector,
            Customers.address
        )
        
    @start_db_transaction
    async def add(self,data:AddCustomerDbSchema):

        self.session.add(Customers(**data.model_dump(mode='json')))

        return True
        
    @start_db_transaction  
    async def update(self,data:UpdateCustomerDbSchema):
        data_toupdate=data.model_dump(mode='json',exclude=['customer_id'],exclude_none=True,exclude_unset=True)

        if not data_toupdate or len(data_toupdate)<1:
            return False
        
        customer_toupdate=update(Customers).where(Customers.id==data.customer_id).values(
            **data_toupdate
        ).returning(Customers.id)

        is_updated=(await self.session.execute(customer_toupdate)).scalar_one_or_none()
        
        return is_updated
        
    @start_db_transaction
    async def delete(self,customer_id:str):
        have_order=(await self.session.execute(select(Orders.id).where(Orders.customer_id==customer_id).limit(1))).scalar_one_or_none()
        if have_order:
            return False
        
        customer_todelete=delete(Customers).where(Customers.id==customer_id).returning(Customers.id)
        is_deleted=(await self.session.execute(customer_todelete)).scalar_one_or_none()
        
        return is_deleted
        

    async def get(self,offset:int=1,limit:int=10,query:str=''):
        search_term=f"%{query.lower()}%"
        cursor=(offset-1)*limit
        date_expr=func.date(func.timezone("Asia/Kolkata",Customers.created_at))
        queried_customers=(await self.session.execute(
            select(
                *self.customer_cols,
                date_expr.label("customer_created_at")
            ).limit(limit)
            .where(
                or_(
                    Customers.id.ilike(search_term),
                    Customers.name.ilike(search_term),
                    Customers.email.ilike(search_term),
                    Customers.address.ilike(search_term),
                    Customers.industry.ilike(search_term),
                    func.cast(Customers.created_at,String).ilike(search_term),
                    Customers.website_url.ilike(search_term),
                    Customers.mobile_number.ilike(search_term),
                    Customers.sector.ilike(search_term),
                    Customers.gst_number.ilike(search_term)

                ),
                Customers.sequence_id>cursor
            )
        )).mappings().all()

        total_customers:int=0
        if offset==1:
            total_customers=(await self.session.execute(
                select(func.count(Customers.id))
            )).scalar_one_or_none()

        return {
            'customers':queried_customers,
            'total_customers':total_customers,
            'total_pages':ceil(total_customers/limit)
        }
        
    
    async def search(self,query:str):
        search_term=f"%{query.lower()}%"
        queried_customers=(await self.session.execute(
            select(
                Customers.id,
                Customers.name,
            ).where(
                or_(
                    Customers.id.ilike(search_term),
                    Customers.name.ilike(search_term),
                    Customers.email.ilike(search_term),
                    Customers.address.ilike(search_term),
                    Customers.industry.ilike(search_term),
                    func.cast(Customers.created_at,String).ilike(search_term),
                    Customers.website_url.ilike(search_term),
                    Customers.mobile_number.ilike(search_term),
                    Customers.sector.ilike(search_term),
                    Customers.gst_number.ilike(search_term)
                )
            )
            .limit(5)
        )).mappings().all()

        return {'customers':queried_customers}

       
    async def get_by_id(self,customer_id:str):
        date_expr=func.date(func.timezone("Asia/Kolkata",Customers.created_at))
        queried_customers=(await self.session.execute(
            select(
                *self.customer_cols,
                date_expr.label("customer_created_at")
            )
            .where(Customers.id==customer_id)
        )).mappings().one_or_none()
        
        return {'customer':queried_customers}



