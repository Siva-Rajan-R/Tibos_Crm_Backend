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
from ..models.user import Users
from schemas.db_schemas.contact import AddContactDbSchema,UpdateContactDbSchema
from models.response_models.req_res_models import SuccessResponseTypDict,BaseResponseTypDict,ErrorResponseTypDict



class ContactsRepo(BaseRepoModel):
    """on this calss have a multiple methods"""
    def __init__(self,session:AsyncSession,user_role:UserRoles,cur_user_id:str):
        self.session=session
        self.user_role=user_role
        self.cur_user_id=cur_user_id
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
            return ErrorResponseTypDict(status_code=400,success=False,msg="Error : Updating Contact",description="No data provided for update")
        
        contact_toupdate=update(Contacts).where(Contacts.id==data.contact_id,Contacts.customer_id==data.customer_id).values(
            **data_toupdate
        ).returning(Contacts.id)

        is_updated=(await self.session.execute(contact_toupdate)).scalar_one_or_none()

        return is_updated if is_updated else ErrorResponseTypDict(status_code=400,success=False,msg="Error : Updating Contact",description="Unable to update the contact, may be invalid contact id or customer id")


    @start_db_transaction
    async def delete(self,customer_id:str,contact_id:str,soft_delete:bool=True):
        if soft_delete:
            contact_todelete=update(Contacts).where(Contacts.id==contact_id,Contacts.customer_id==customer_id,Contacts.is_deleted==False).values(
                is_deleted=True,
                deleted_at=func.now(),
                deleted_by=self.cur_user_id
            ).returning(Contacts.id)
            is_deleted=(await self.session.execute(contact_todelete)).scalar_one_or_none()
        
        else:
            if self.user_role if isinstance(self.user_role,UserRoles) else self.user_role!=UserRoles.SUPER_ADMIN.value:
                return ErrorResponseTypDict(status_code=403,success=False,msg="Error : Deleting Contact",description="Only super admin can perform hard delete operation")
            have_order=(await self.session.execute(select(Orders.id).where(Orders.customer_id==contact_id).limit(1))).scalar_one_or_none()
            if have_order:
                return ErrorResponseTypDict(status_code=400,success=False,msg="Error : Deleting Contact",description="Cannot delete contact associated with existing orders. Please delete associated orders first.")
            contact_todelete=delete(Contacts).where(Contacts.id==contact_id,Contacts.customer_id==customer_id).returning(Contacts.id)
            is_deleted=(await self.session.execute(contact_todelete)).scalar_one_or_none()

        return is_deleted if is_deleted else ErrorResponseTypDict(status_code=400,success=False,msg="Error : Deleting Contact",description="Unable to delete the contact, may be invalid contact id or customer id")
        
    @start_db_transaction
    async def recover(self,customer_id:str,contact_id:str):
        if self.user_role if isinstance(self.user_role,UserRoles) else self.user_role!=UserRoles.SUPER_ADMIN.value:
            return ErrorResponseTypDict(status_code=403,success=False,msg="Error : Recovering Contact",description="Only super admin can perform recover operation")
        
        contact_torecover=update(Contacts).where(Contacts.id==contact_id,Contacts.customer_id==customer_id,Contacts.is_deleted==True).values(
            is_deleted=False
        ).returning(Contacts.id)
        is_recovered=(await self.session.execute(contact_torecover)).scalar_one_or_none()
        return is_recovered if is_recovered else ErrorResponseTypDict(status_code=400,success=False,msg="Error : Recovering Contact",description="Unable to recover the contact, may contact is not deleted or already recovered")
        

    async def get(self,offset:int,limit:int,query:str='',include_deleted:bool=False):
        search_term=f"%{query.lower()}%"
        cursor=(offset-1)*limit
        date_expr=func.date(func.timezone("Asia/Kolkata",Contacts.created_at))
        deleted_at=func.date(func.timezone("Asia/Kolkata",Contacts.deleted_at))
        cols=[
            *self.contact_cols
        ]
        if include_deleted:
            cols.extend([Users.name.label('deleted_by'),deleted_at.label('deleted_at')])

        queried_contacts=(await self.session.execute(
            select(
                *cols,
                date_expr.label("contact_created_at")
            )
            .join(Customers,Customers.id==Contacts.customer_id,isouter=True)
            .join(Users,Users.id==Contacts.deleted_by,isouter=True)
            .limit(limit)
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
                Contacts.sequence_id>cursor,
                Contacts.is_deleted==include_deleted
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
                Contacts.is_deleted==False
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
            .where(Contacts.id==contact_id,Contacts.is_deleted==False)
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
                Contacts.sequence_id>cursor,
                Contacts.is_deleted==False
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



