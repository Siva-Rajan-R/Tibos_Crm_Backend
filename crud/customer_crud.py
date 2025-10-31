from globals.fastapi_globals import HTTPException
from database.models.pg_models.customer import Customers,CustomerIndustries,CustomerSectors
from utils.uuid_generator import generate_uuid
from sqlalchemy import select,delete,update
from sqlalchemy.ext.asyncio import AsyncSession
from icecream import ic
from data_formats.enums.common_enums import UserRoles
from pydantic import EmailStr
from typing import Optional,List



class CustomersCrud:
    def __init__(self,session:AsyncSession,user_email:EmailStr,user_role:UserRoles):
        self.session=session
        self.user_email=user_email
        self.user_role=user_role

        if self.user_email!="" or self.user_role!=UserRoles.ADMIN:
            raise HTTPException(
                status_code=401,
                detail="Not a valid user"
            )

    async def add(self,name:str,mobile_no:str,email:EmailStr,web_url:Optional[str],no_of_emply:int,gst_no:Optional[str],industry:CustomerIndustries,sector:CustomerSectors,primary_contact:List[str],address:str):
        try:
            async with self.session.begin():
                customer_id=generate_uuid(data=name)
                customer_toadd=Customers(
                    id=customer_id,
                    name=name,
                    mobile_number=mobile_no,
                    email=email,
                    website_url=web_url,
                    no_of_employee=no_of_emply,
                    gst_number=gst_no,
                    industry=industry,
                    sector=sector,
                    primary_contact=primary_contact,
                    address=address
                )

                self.session.add(customer_toadd)

                return "Successfully Customer Added"
        
        except HTTPException:
            raise

        except Exception as e:
            ic(f"Something went wrong while adding customer {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Something went wrong while adding customer {e}"
            )
        
    async def update(self,customer_id:str,name:str,mobile_no:str,email:EmailStr,web_url:Optional[str],no_of_emply:int,gst_no:Optional[str],industry:CustomerIndustries,sector:CustomerSectors,primary_contact:List[str],address:str):
        try:
            async with self.session.begin():
                customer_toupdate=update(Customers).where(Customers.id==customer_id).values(
                    name=name,
                    mobile_number=mobile_no,
                    email=email,
                    website_url=web_url,
                    no_of_employee=no_of_emply,
                    gst_number=gst_no,
                    industry=industry,
                    sector=sector,
                    primary_contact=primary_contact,
                    address=address
                ).returning(Customers.id)

                customer_id=(await self.session.execute(customer_toupdate)).scalar_one_or_none()

                if not customer_id:
                    raise HTTPException(
                        status_code=404,
                        detail="Invalid Customer Id"
                    )
                
                return "Customer Update Successfully"
        
        except HTTPException:
            raise

        except Exception as e:
            ic(f"Something went wrong while updating customer {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Something went wrong while updating customer {e}"
            )
        
    async def delete(self,customer_id:str):
        try:
            async with self.session.begin():
                customer_todelete=delete(Customers).where(Customers.id==customer_id).returning(Customers.id)

                customer_id=(await self.session.execute(customer_todelete)).scalar_one_or_none()

                if not customer_id:
                    raise HTTPException(
                        status_code=404,
                        detail="Invalid Customer Id"
                    )
                
                return "Customer Deleted Successfully"
        
        except HTTPException:
            raise

        except Exception as e:
            ic(f"Something went wrong while Deleting customer {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Something went wrong while Deleting customer {e}"
            )
        
    async def get(self):
        try:
            queried_customers=(await self.session.execute(
                select(
                    Customers.id,
                    Customers.name,
                    Customers.mobile_number,
                    Customers.email,
                    Customers.gst_number,
                    Customers.no_of_employee,
                    Customers.website_url,
                    Customers.industry,
                    Customers.sector,
                    Customers.primary_contact,
                    Customers.address
                )
            )).mappings().all()

            return {'customers':queried_customers}
        
        except HTTPException:
            raise
        
        except Exception as e:
            ic(f"Something went wrong while fetching all customers {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Something went wrong while fetching all customers {e}"
            )
        
    async def get_by_id(self,customer_id:str):
        try:
            queried_customers=(await self.session.execute(
                select(
                    Customers.id,
                    Customers.name,
                    Customers.mobile_number,
                    Customers.email,
                    Customers.gst_number,
                    Customers.no_of_employee,
                    Customers.website_url,
                    Customers.industry,
                    Customers.sector,
                    Customers.primary_contact,
                    Customers.address
                )
                .where(Customers.id==customer_id)
            )).mappings().one_or_none()
           
            return {'customer':queried_customers}
        
        except HTTPException:
            raise
        
        except Exception as e:
            ic(f"Something went wrong while fetching single customer {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Something went wrong while fetching single customer {e}"
            )



