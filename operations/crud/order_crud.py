from globals.fastapi_globals import HTTPException
from database.models.pg_models.order import Orders
from database.models.pg_models.product import Products
from database.models.pg_models.customer import Customers
from utils.uuid_generator import generate_uuid
from sqlalchemy import select,delete,update,or_,func
from sqlalchemy.ext.asyncio import AsyncSession
from icecream import ic
from data_formats.enums.common_enums import UserRoles
from data_formats.enums.pg_enums import PaymentStatus,InvoiceStatus
from data_formats.typed_dicts.pg_dict import DeliveryInfo
from operations.abstract_models.crud_model import BaseCrud



class OrdersCrud(BaseCrud):
    def __init__(self,session:AsyncSession,user_role:UserRoles):
        self.session=session
        self.user_role=user_role

        if self.user_role==UserRoles.USER.value:
            raise HTTPException(
                status_code=401,
                detail="Not a valid user"
            )

    async def add(self,customer_id:str,product_id:str,qty:int,total_price:float,discount_price:float,final_price:float,delivery_info:DeliveryInfo,payment_status:PaymentStatus,invoice_status:InvoiceStatus):
        try:
            async with self.session.begin():
                order_id=generate_uuid(data=customer_id)
                order_toadd=Orders(
                    id=order_id,
                    product_id=product_id,
                    customer_id=customer_id,
                    quantity=qty,
                    total_price=total_price,
                    discount_price=discount_price,
                    final_price=final_price,
                    delivery_info=delivery_info,
                    payment_status=payment_status.value,
                    invoice_status=invoice_status.value
                )

                self.session.add(order_toadd)
                # need to implement invoice generation process + email sending
                return "Successfully Order Added"
        
        except HTTPException:
            raise

        except Exception as e:
            ic(f"Something went wrong while adding order {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Something went wrong while adding order {e}"
            )
        
    async def update(self,order_id:str,customer_id:str,product_id:str,qty:int,total_price:float,discount_price:float,final_price:float,delivery_info:DeliveryInfo,payment_status:PaymentStatus,invoice_status:InvoiceStatus):
        try:
            async with self.session.begin():
                order_toupdate=update(Orders).where(Orders.id==order_id,Orders.customer_id==customer_id).values(
                    product_id=product_id,
                    customer_id=customer_id,
                    quantity=qty,
                    total_price=total_price,
                    discount_price=discount_price,
                    final_price=final_price,
                    delivery_info=delivery_info,
                    payment_status=payment_status.value,
                    invoice_status=invoice_status.value
                ).returning(Orders.id)

                order_id=(await self.session.execute(order_toupdate)).scalar_one_or_none()

                if not order_id:
                    raise HTTPException(
                        status_code=404,
                        detail="Invalid Order or Customer Id"
                    )
                
                # need to implement invoice generation process + email sending
                return "Order Update Successfully"
        
        except HTTPException:
            raise

        except Exception as e:
            ic(f"Something went wrong while updating Order {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Something went wrong while updating Order {e}"
            )
        
    async def delete(self,order_id:str,customer_id:str):
        try:
            async with self.session.begin():
                order_todelete=delete(Orders).where(Orders.id==order_id,Orders.customer_id==customer_id).returning(Orders.id)

                order_id=(await self.session.execute(order_todelete)).scalar_one_or_none()

                if not order_id:
                    raise HTTPException(
                        status_code=404,
                        detail="Invalid Order or Customer Id"
                    )
                
                # need to implement email sending "Your orders has been stoped from CRM"
                return "Order Deleted Successfully"
        
        except HTTPException:
            raise

        except Exception as e:
            ic(f"Something went wrong while Deleting Order {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Something went wrong while Deleting Order {e}"
            )
       
    async def get(self,offset:int=1,limit:int=10,query:str=''):
        try:
            search_term=f"%{query.lower()}%"
            cursor=(offset-1)*limit
            queried_orders=(await self.session.execute(
                select(
                    Orders.id,
                    Orders.customer_id,
                    Orders.product_id,
                    Orders.quantity,
                    Orders.total_price,
                    Orders.discount_price,
                    Orders.final_price,
                    Orders.delivery_info,
                    Orders.payment_status,
                    Orders.invoice_status,
                    Products.name.label('product_name'),
                    Products.product_type,
                    Products.description,
                    Customers.name.label('customer_name'),
                    Customers.mobile_number  
                )
                .join(Products,Products.id==Orders.product_id,isouter=True)
                .join(Customers,Customers.id==Orders.customer_id,isouter=True)
                .limit(limit)
                .where(
                    or_(
                        Orders.id.ilike(search_term),
                        Products.name.ilike(search_term),
                        Products.id.ilike(search_term),
                        Customers.name.ilike(search_term),
                        Customers.email.ilike(search_term)
                    ),
                    Orders.sequence_id>cursor
                )
            )).mappings().all()

            total_orders:int=0
            total_revenue=0
            highest_revenue=0
            ic(offset)
            if offset==1:
                total_orders=(await self.session.execute(
                    func.count(Orders.id)
                )).scalar_one_or_none()

                total_revenue=(await self.session.execute(
                    func.sum(Orders.final_price)
                )).scalar_one_or_none()

                highest_revenue=(await self.session.execute(
                    select(func.max(Orders.final_price))
                )).scalar()

            return {
                'orders':queried_orders,
                'total_orders':total_orders,
                'total_pages':total_orders//limit,
                'total_revenue':total_revenue,
                'highest_revenue':highest_revenue
            }
        
        except HTTPException:
            raise
        
        except Exception as e:
            ic(f"Something went wrong while fetching all orders {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Something went wrong while fetching all orders {e}"
            )
    
    async def search(self,query:str):
        try:
            search_term=f"%{query.lower()}%"
            queried_orders=(await self.session.execute(
                select(
                    Orders.id,
                    Orders.customer_id,
                    Orders.product_id,
                    Orders.quantity,
                    Orders.total_price,
                    Orders.discount_price,
                    Orders.final_price,
                    Orders.delivery_info,
                    Orders.invoice_status,
                    Orders.payment_status,
                    Products.name.label('product_name'),
                    Products.product_type,
                    Products.description,
                    Customers.name.label('customer_name'),
                    Customers.mobile_number  
                )
                .join(Products,Products.id==Orders.product_id,isouter=True)
                .join(Customers,Customers.id==Orders.customer_id,isouter=True)
                .where(or_(Orders.id.ilike(search_term),Products.name.ilike(search_term),Customers.name.ilike(search_term)))
                .limit(5)
            )).mappings().all()

            return {'orders':queried_orders}
        
        except HTTPException:
            raise
        
        except Exception as e:
            ic(f"Something went wrong while searching orders {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Something went wrong while searching orders {e}"
            )
        
    async def get_by_id(self,order_id:str):
        try:
            queried_orders=(await self.session.execute(
                select(
                    Orders.id,
                    Orders.customer_id,
                    Orders.product_id,
                    Orders.quantity,
                    Orders.total_price,
                    Orders.discount_price,
                    Orders.final_price,
                    Orders.delivery_info,
                    Orders.payment_status,
                    Orders.invoice_status,
                    Products.name,
                    Products.product_type,
                    Products.description,
                    Customers.name,
                    Customers.mobile_number  
                )
                .join(Products,Products.id==Orders.product_id,isouter=True)
                .join(Customers,Customers.id==Orders.customer_id,isouter=True)
                .where(Orders.id==order_id)
            )).mappings().one_or_none()

            return {'order':queried_orders}
        
        except HTTPException:
            raise
        
        except Exception as e:
            ic(f"Something went wrong while fetching single order {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Something went wrong while fetching single order {e}"
            )
    
    async def get_by_customer_id(self,customer_id:str,offset:int,limit:int):
        try:
            cursor=(offset-1)*limit
            queried_orders=(await self.session.execute(
                select(
                    Orders.id,
                    Orders.customer_id,
                    Orders.product_id,
                    Orders.quantity,
                    Orders.total_price,
                    Orders.discount_price,
                    Orders.final_price,
                    Orders.delivery_info,
                    Orders.payment_status,
                    Orders.invoice_status,
                    Products.name,
                    Products.product_type,
                    Products.description,
                    Customers.name,
                    Customers.mobile_number  
                )
                .join(Products,Products.id==Orders.product_id,isouter=True)
                .join(Customers,Customers.id==Orders.customer_id,isouter=True)
                .where(Orders.customer_id==customer_id,Orders.sequence_id>cursor)
                .limit(limit)
            )).mappings().all()

            total_orders:int=0
            total_revenue:int=0
            highest_revenue:int=0
            if offset==1:
                total_orders=(await self.session.execute(
                    select(func.count(Orders.id))
                    .where(Orders.customer_id==customer_id)
                )).scalar_one_or_none()

                total_revenue=(await self.session.execute(
                    select(func.sum(Orders.final_price))
                    .where(Orders.customer_id==customer_id)
                )).scalar_one_or_none()

                highest_revenue=(await self.session.execute(
                    select(func.max(Orders.final_price))
                    .where(Orders.customer_id==customer_id)
                )).scalar()

            return {
                'orders':queried_orders,
                'total_orders':total_orders,
                'total_pages':total_orders//limit,
                'total_revenue':total_revenue,
                'highest_revenue':highest_revenue
            }
        
        except HTTPException:
            raise
        
        except Exception as e:
            ic(f"Something went wrong while fetching customer order {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Something went wrong while fetching customer order {e}"
            )



