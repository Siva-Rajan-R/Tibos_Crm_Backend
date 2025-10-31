from globals.fastapi_globals import HTTPException
from database.models.pg_models.contact import Contacts
from database.models.pg_models.customer import Customers
from utils.uuid_generator import generate_uuid
from sqlalchemy import select,delete,update
from sqlalchemy.ext.asyncio import AsyncSession
from icecream import ic
from data_formats.enums.common_enums import UserRoles
from pydantic import EmailStr
from typing import Optional,List



class ContactsCrud:
    """on this calss have a multiple methods"""
    def __init__(self,session:AsyncSession,user_email:EmailStr,user_role:UserRoles):
        self.session=session
        self.user_email=user_email
        self.user_role=user_role

        if self.user_email!="" or self.user_role!=UserRoles.ADMIN:
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
                contact_toupdate=update(Contacts).where(Contacts.id==contact_id).values(
                    customer_id=customer_id,
                    name=name,
                    mobile_number=mobile_no,
                    email=email
                ).returning(Contacts.id)

                contact_id=(await self.session.execute(contact_toupdate)).scalar_one_or_none()

                if not contact_id:
                    raise HTTPException(
                        status_code=404,
                        detail="Invalid Contact Id"
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
        
    async def delete(self,contact_id:str):
        try:
            async with self.session.begin():
                contact_todelete=delete(Contacts).where(Contacts.id==contact_id).returning(Contacts.id)

                contact_id=(await self.session.execute(contact_todelete)).scalar_one_or_none()

                if not contact_id:
                    raise HTTPException(
                        status_code=404,
                        detail="Invalid Contact Id"
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
        
    async def get(self):
        try:
            queried_contacts=(await self.session.execute(
                select(
                    Contacts.id,
                    Contacts.customer_id,
                    Contacts.name,Contacts.email,
                    Contacts.mobile_number,
                    Customers.name,
                    Customers.email,
                    Customers.website_url  
                )
                .join(Customers,Customers.id==Contacts.customer_id,isouter=True,full=True)
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
        
    async def get_by_id(self,contact_id:str):
        try:
            queried_contacts=(await self.session.execute(
                select(
                    Contacts.id,
                    Contacts.customer_id,
                    Contacts.name,Contacts.email,
                    Contacts.mobile_number,
                    Customers.name,
                    Customers.email,
                    Customers.website_url  
                )
                .join(Customers,Customers.id==Contacts.customer_id,isouter=True,full=True)
                .where(Contacts.id==contact_id)
            )).mappings().all()

            return {'contact':queried_contacts}
        
        except HTTPException:
            raise
        
        except Exception as e:
            ic(f"Something went wrong while fetching single contact {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Something went wrong while fetching single contact {e}"
            )



