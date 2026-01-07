from . import HTTPException,BaseRepoModel
from ..models.order import Orders
from ..models.product import Products
from ..models.customer import Customers
from core.utils.uuid_generator import generate_uuid
from sqlalchemy import select,delete,update,or_,func,String
from sqlalchemy.ext.asyncio import AsyncSession
from icecream import ic
from core.data_formats.enums.common_enums import UserRoles
from core.data_formats.enums.pg_enums import PaymentStatus,InvoiceStatus
from core.data_formats.typed_dicts.pg_dict import DeliveryInfo
from schemas.db_schemas.order import AddOrderDbSchema,UpdateOrderDbSchema
from core.decorators.db_session_handler_dec import start_db_transaction
from math import ceil



class OrdersRepo(BaseRepoModel):
    def __init__(self,session:AsyncSession,user_role:UserRoles):
        self.session=session
        self.user_role=user_role
        self.orders_cols=(
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


    @start_db_transaction
    async def add(self,data:AddOrderDbSchema):
        self.session.add(Orders(**data.model_dump(mode='json')))
        # need to implement invoice generation process + email sending
        return True
    
    @start_db_transaction
    async def update(self,data:UpdateOrderDbSchema):
        data_toupdate=data.model_dump(mode='json',exclude=['product_id','customer_id','order_id'],exclude_none=True,exclude_unset=True)
        if not data_toupdate or len(data_toupdate)<1:
            return False
        
        order_toupdate=update(Orders).where(Orders.id==data.order_id,Orders.customer_id==data.customer_id).values(
            **data_toupdate
        ).returning(Orders.id)

        is_updated=(await self.session.execute(order_toupdate)).scalar_one_or_none()
        
        # need to implement invoice generation process + email sending
        return is_updated

    @start_db_transaction    
    async def delete(self,order_id:str,customer_id:str):
        order_todelete=delete(Orders).where(Orders.id==order_id,Orders.customer_id==customer_id).returning(Orders.id)

        is_deleted=(await self.session.execute(order_todelete)).scalar_one_or_none()
        
        # need to implement email sending "Your orders has been stoped from CRM"
        return is_deleted


    async def get(self,offset:int=1,limit:int=10,query:str=''):
        search_term=f"%{query.lower()}%"
        cursor=(offset-1)*limit
        date_expr=func.date(func.timezone("Asia/Kolkata",Orders.created_at))
        queried_orders=(await self.session.execute(
            select(
                *self.orders_cols,
                date_expr.label("order_created_at") 
            )
            .join(Products,Products.id==Orders.product_id,isouter=True)
            .join(Customers,Customers.id==Orders.customer_id,isouter=True)
            .limit(limit)
            .where(
                or_(
                    Orders.id.ilike(search_term),
                    Products.name.ilike(search_term),
                    Products.id.ilike(search_term),
                    Products.product_type.ilike(search_term),
                    Customers.name.ilike(search_term),
                    Customers.email.ilike(search_term),
                    Customers.mobile_number.ilike(search_term),
                    func.cast(Orders.created_at,String).ilike(search_term),
                    Orders.invoice_status.ilike(search_term),
                    Orders.payment_status.ilike(search_term),
                ),
                Orders.sequence_id>cursor
            )
        )).mappings().all()

        total_orders:int=0
        total_revenue=0
        highest_revenue=0
        pending_dues=0
        pending_invoice=0
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
            pending_invoice=(
                await self.session.execute(
                    select(
                        func.count().filter(Orders.invoice_status == InvoiceStatus.INCOMPLETED.value).label("pending_invoices"))
                    )
            ).scalar_one_or_none()
            pending_dues=(
                await self.session.execute(
                    select(func.count().filter(Orders.payment_status == PaymentStatus.NOT_PAID.value).label("pending_dues"))
                )
            ).scalar_one_or_none()

        return {
            'orders':queried_orders,
            'total_orders':total_orders,
            'total_pages':ceil(total_orders/limit),
            'total_revenue':total_revenue,
            'highest_revenue':highest_revenue,
            'pending_invoice':pending_invoice,
            'pending_dues':pending_dues
        }
    
    async def search(self,query:str):
        search_term=f"%{query.lower()}%"
        date_expr=func.date(func.timezone("Asia/Kolkata",Orders.created_at))
        queried_orders=(await self.session.execute(
            select(
                *self.orders_cols,
                date_expr.label("order_created_at")  
            )
            .join(Products,Products.id==Orders.product_id,isouter=True)
            .join(Customers,Customers.id==Orders.customer_id,isouter=True)
            .where(
                or_(
                    Orders.id.ilike(search_term),
                    Products.name.ilike(search_term),
                    Products.id.ilike(search_term),
                    Products.product_type.ilike(search_term),
                    Customers.name.ilike(search_term),
                    Customers.email.ilike(search_term),
                    Customers.mobile_number.ilike(search_term),
                    func.cast(Orders.created_at,String).ilike(search_term),
                    Orders.invoice_status.ilike(search_term),
                    Orders.payment_status.ilike(search_term),
                ),
            )
            .limit(5)
        )).mappings().all()

        return {'orders':queried_orders}

        
    async def get_by_id(self,order_id:str):
        date_expr=func.date(func.timezone("Asia/Kolkata",Orders.created_at))
        queried_orders=(await self.session.execute(
            select(
                *self.orders_cols,
                date_expr.label("order_created_at")  
            )
            .join(Products,Products.id==Orders.product_id,isouter=True)
            .join(Customers,Customers.id==Orders.customer_id,isouter=True)
            .where(Orders.id==order_id)
        )).mappings().one_or_none()

        return {'order':queried_orders}
        
    
    async def get_by_customer_id(self,customer_id:str,offset:int,limit:int):
        cursor=(offset-1)*limit
        date_expr=func.date(func.timezone("Asia/Kolkata",Orders.created_at))
        queried_orders=(await self.session.execute(
            select(
                *self.orders_cols,
                date_expr.label("order_created_at")   
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
            'total_pages':ceil(total_orders/limit),
            'total_revenue':total_revenue,
            'highest_revenue':highest_revenue
        }



