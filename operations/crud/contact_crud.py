from globals.fastapi_globals import HTTPException
from database.models.pg_models.contact import Contacts
from database.models.pg_models.customer import Customers
from utils.uuid_generator import generate_uuid
from sqlalchemy import select,delete,update,or_
from sqlalchemy.ext.asyncio import AsyncSession
from icecream import ic
from data_formats.enums.common_enums import UserRoles
from pydantic import EmailStr
from typing import Optional,List
from operations.abstract_models.crud_model import BaseCrud



class ContactsCrud(BaseCrud):
    """on this calss have a multiple methods"""
    def __init__(self,session:AsyncSession,user_role:UserRoles):
        self.session=session
        self.user_role=user_role

        if self.user_role==UserRoles.USER.value:
            raise HTTPException(
                status_code=401,
                detail="Not a valid user"
            )

    async def add(self,name:str,customer_id:str,mobile_no:str,email:EmailStr):
        """using this method we can add the contacts to the db"""
        try:
            async with self.session.begin():
                contact_id=generate_uuid(data=name)
                contact_toadd=Contacts(
                    id=contact_id,
                    customer_id=customer_id,
                    name=name,
                    mobile_number=mobile_no,
                    email=email
                    
                )

                self.session.add(contact_toadd)

                return "Successfully Contact Added"
        
        except HTTPException:
            raise

        except Exception as e:
            ic(f"Something went wrong while adding Contact {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Something went wrong while adding Contact {e}"
            )
        
    async def update(self,contact_id:str,name:str,customer_id:str,mobile_no:str,email:EmailStr):
        try:
            async with self.session.begin():
                contact_toupdate=update(Contacts).where(Contacts.id==contact_id,Contacts.customer_id==customer_id).values(
                    customer_id=customer_id,
                    name=name,
                    mobile_number=mobile_no,
                    email=email
                ).returning(Contacts.id)

                contact_id=(await self.session.execute(contact_toupdate)).scalar_one_or_none()

                if not contact_id:
                    raise HTTPException(
                        status_code=404,
                        detail="Invalid Contact or Customer Id"
                    )
                
                return "Contact Update Successfully"
        
        except HTTPException:
            raise

        except Exception as e:
            ic(f"Something went wrong while updating Contact {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Something went wrong while updating Contact {e}"
            )
        
    async def delete(self,customer_id:str,contact_id:str):
        try:
            async with self.session.begin():
                contact_todelete=delete(Contacts).where(Contacts.id==contact_id,Contacts.customer_id==customer_id).returning(Contacts.id)

                contact_id=(await self.session.execute(contact_todelete)).scalar_one_or_none()

                if not contact_id:
                    raise HTTPException(
                        status_code=404,
                        detail="Invalid Contact or Customer Id"
                    )
                
                return "Contact Deleted Successfully"
        
        except HTTPException:
            raise

        except Exception as e:
            ic(f"Something went wrong while Deleting contact {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Something went wrong while Deleting contact {e}"
            )
        
    async def get(self,offset:int,limit:int,query:str=''):
        try:
            search_term=f"%{query.lower()}%"
            queried_contacts=(await self.session.execute(
                select(
                    Contacts.id,
                    Contacts.customer_id,
                    Contacts.name.label('contact_name'),
                    Contacts.email.label('contact_email'),
                    Contacts.mobile_number.label('contact_mobile'),
                    Customers.name.label('customer_name'),
                    Customers.email.label('customer_email'),
                    Customers.website_url.label('customer_website')  
                )
                .join(Customers,Customers.id==Contacts.customer_id,isouter=True).offset(offset).limit(limit)
                .where(
                    or_(
                        Contacts.name.ilike(search_term),
                        Contacts.id.ilike(search_term),
                        Contacts.email.ilike(search_term)
                    )
                )
            )).mappings().all()

            return {'contacts':queried_contacts}
        
        except HTTPException:
            raise
        
        except Exception as e:
            ic(f"Something went wrong while fetching all contacts {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Something went wrong while fetching all contacts {e}"
            )
        
    async def search(self,query:str):
        try:
            search_term=f"%{query.lower()}%"
            queried_contacts=(await self.session.execute(
                select(
                    Contacts.id,
                    Contacts.name.label('contact_name'), 
                ).where(
                    Contacts.name.ilike(search_term)
                ).limit(5)
            )).mappings().all()

            return {'contacts':queried_contacts}
        
        except HTTPException:
            raise
        
        except Exception as e:
            ic(f"Something went wrong while searching contacts {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Something went wrong while searching contacts {e}"
            )
        
    async def get_by_id(self,contact_id:str):
        try:
            queried_contacts=(await self.session.execute(
                select(
                    Contacts.id,
                    Contacts.customer_id,
                    Contacts.name.label('contact_name'),
                    Contacts.email.label('contact_email'),
                    Contacts.mobile_number.label('contact_mobile'),
                    Customers.name.label('customer_name'),
                    Customers.email.label('customer_email'),
                    Customers.website_url.label('customer_website')  
                )
                .join(Customers,Customers.id==Contacts.customer_id,isouter=True)
                .where(Contacts.id==contact_id)
            )).mappings().one_or_none()

            return {'contact':queried_contacts}
        
        except HTTPException:
            raise
        
        except Exception as e:
            ic(f"Something went wrong while fetching single contact {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Something went wrong while fetching single contact {e}"
            )
    
    async def get_by_customer_id(self,customer_id:str,offset:int,limit:int):
        try:
            queried_contacts=(await self.session.execute(
                select(
                    Contacts.id,
                    Contacts.customer_id,
                    Contacts.name.label('contact_name'),
                    Contacts.email.label('contact_email'),
                    Contacts.mobile_number.label('contact_mobile'),
                    Customers.name.label('customer_name'),
                    Customers.email.label('customer_email'),
                    Customers.website_url.label('customer_website')  
                )
                .join(Customers,Customers.id==Contacts.customer_id,isouter=True)
                .where(customer_id==Contacts.customer_id)
                .offset(offset)
                .limit(limit)
            )).mappings().all()

            return {'contacts':queried_contacts}
        
        except HTTPException:
            raise
        
        except Exception as e:
            ic(f"Something went wrong while fetching Cusotmer contact {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Something went wrong while fetching Cusotmer contact {e}"
            )



