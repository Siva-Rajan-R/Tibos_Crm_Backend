from .import HTTPException,BaseRepoModel
from ..models.contact import Contacts
from ..models.order import Orders
from ..models.customer import Customers
from core.utils.uuid_generator import generate_uuid
from sqlalchemy import select,delete,update,or_,func,String
from sqlalchemy.ext.asyncio import AsyncSession
from icecream import ic
from core.data_formats.enums.common_enums import UserRoles
from pydantic import EmailStr
from typing import Optional,List
from math import ceil
from core.decorators.db_session_handler_dec import start_db_transaction
from core.decorators.error_handler_dec import catch_errors
from schemas.db_schemas.contact import AddContactDbSchema,UpdateContactDbSchema



class ContactsRepo(BaseRepoModel):
    """on this calss have a multiple methods"""
    def __init__(self,session:AsyncSession,user_role:UserRoles):
        self.session=session
        self.user_role=user_role
        self.contact_cols=(
            Contacts.id,
            Contacts.customer_id,
            Contacts.name.label('contact_name'),
            Contacts.email.label('contact_email'),
            Contacts.mobile_number.label('contact_mobile'),
            Customers.name.label('customer_name'),
            Customers.email.label('customer_email'),
            Customers.website_url.label('customer_website')
        )

    async def is_contact_exists(self,email:EmailStr,mobile_number:str,customer_id:str):
        is_exists=(await self.session.execute(
            select(Contacts.id)
            .where(
                Contacts.customer_id==customer_id,
                or_(
                    Contacts.email==email,
                    Contacts.mobile_number==mobile_number
                )
            )
        )).scalar_one_or_none()

        return is_exists

    @start_db_transaction
    async def add(self,data:AddContactDbSchema):
        """using this method we can add the contacts to the db"""
        self.session.add(Contacts(**data.model_dump(mode='json')))
        return True
        
    @start_db_transaction   
    async def update(self,data:UpdateContactDbSchema):
        data_toupdate=data.model_dump(mode='json',exclude=['contact_id','customer_id'],exclude_unset=True,exclude_none=True)
        if not data_toupdate or len(data_toupdate)<1:
            return False
        
        contact_toupdate=update(Contacts).where(Contacts.id==data.contact_id,Contacts.customer_id==data.customer_id).values(
            **data_toupdate
        ).returning(Contacts.id)

        is_updated=(await self.session.execute(contact_toupdate)).scalar_one_or_none()

        return is_updated
        
    @start_db_transaction
    async def delete(self,customer_id:str,contact_id:str):
        have_order=(await self.session.execute(select(Orders.id).where(Orders.customer_id==contact_id).limit(1))).scalar_one_or_none()
        if have_order:
            return False
        
        contact_todelete=delete(Contacts).where(Contacts.id==contact_id,Contacts.customer_id==customer_id).returning(Contacts.id)

        is_deleted=(await self.session.execute(contact_todelete)).scalar_one_or_none()

        return is_deleted
    
        
    async def get(self,offset:int,limit:int,query:str=''):
        search_term=f"%{query.lower()}%"
        cursor=(offset-1)*limit
        date_expr=func.date(func.timezone("Asia/Kolkata",Contacts.created_at))
        queried_contacts=(await self.session.execute(
            select(
                *self.contact_cols,
                date_expr.label("contact_created_at")
            )
            .join(Customers,Customers.id==Contacts.customer_id,isouter=True).limit(limit)
            .where(
                or_(
                    Contacts.name.ilike(search_term),
                    Contacts.id.ilike(search_term),
                    Contacts.email.ilike(search_term),
                    Contacts.mobile_number.ilike(search_term),
                    func.cast(Contacts.created_at,String).ilike(search_term),
                    Customers.name.ilike(search_term),
                    Customers.email.ilike(search_term),
                    Customers.website_url.ilike(search_term)
                ),
                Contacts.sequence_id>cursor
            )
        )).mappings().all()

        total_contacts:int=0
        if offset==1:
            total_contacts=(await self.session.execute(
                select(func.count(Contacts.id))
            )).scalar_one_or_none()

        return {
            'contacts':queried_contacts,
            'total_contacts':total_contacts,
            'total_pages':ceil(total_contacts/limit)
        }


    async def search(self,query:str):
        search_term=f"%{query.lower()}%"
        queried_contacts=(await self.session.execute(
            select(
                Contacts.id,
                Contacts.name.label('contact_name'), 
            ).where(
                or_(
                    Contacts.name.ilike(search_term),
                    Contacts.id.ilike(search_term),
                    Contacts.email.ilike(search_term),
                    Contacts.mobile_number.ilike(search_term),
                    func.cast(Contacts.created_at,String).ilike(search_term),
                    Customers.name.ilike(search_term),
                    Customers.email.ilike(search_term),
                    Customers.website_url.ilike(search_term)
                ),
            ).limit(5)
        )).mappings().all()

        return {'contacts':queried_contacts}
        
    async def get_by_id(self,contact_id:str):
        date_expr=func.date(func.timezone("Asia/Kolkata",Contacts.created_at))
        queried_contacts=(await self.session.execute(
            select(
                *self.contact_cols,
                date_expr.label("contact_created_at")
            )
            .join(Customers,Customers.id==Contacts.customer_id,isouter=True)
            .where(Contacts.id==contact_id)
        )).mappings().one_or_none()

        return {'contact':queried_contacts}
    
    async def get_by_customer_id(self,customer_id:str,offset:int,limit:int,query:str=''):
        cursor=(offset-1)*limit
        search_term=f"%{query.lower()}%"
        date_expr=func.date(func.timezone("Asia/Kolkata",Contacts.created_at))
        queried_contacts=(await self.session.execute(
            select(
                *self.contact_cols,
                date_expr.label("contact_created_at")


            )
            .join(Customers,Customers.id==Contacts.customer_id,isouter=True)
            .where(
                or_(
                    Contacts.name.ilike(search_term),
                    Contacts.id.ilike(search_term),
                    Contacts.email.ilike(search_term),
                    Contacts.mobile_number.ilike(search_term),
                    func.cast(Contacts.created_at,String).ilike(search_term),
                    Customers.name.ilike(search_term),
                    Customers.email.ilike(search_term),
                    Customers.website_url.ilike(search_term)
                ),
                customer_id==Contacts.customer_id,
                Contacts.sequence_id>cursor
            )
            .limit(limit)
        )).mappings().all()

        total_contacts:int=0
        if offset==1:
            total_contacts=(await self.session.execute(
                select(func.count(Contacts.id))
                .where(customer_id==Contacts.customer_id)
            )).scalar_one_or_none()

        return {
            'contacts':queried_contacts,
            'total_contacts':total_contacts,
            'total_pages':ceil(total_contacts/limit)
        }



