from typing import cast
from . import HTTPException,BaseRepoModel
from ..models.order import Orders
from ..models.product import Products
from ..models.customer import Customers
from ..models.distributor import Distributors
from core.utils.uuid_generator import generate_uuid
from sqlalchemy import Numeric, select,delete,update,or_,func,String,cast,case
from sqlalchemy.ext.asyncio import AsyncSession
from icecream import ic
from core.data_formats.enums.common_enums import UserRoles
from core.data_formats.enums.pg_enums import PaymentStatus,InvoiceStatus
from core.data_formats.typed_dicts.pg_dict import DeliveryInfo
from schemas.db_schemas.order import AddOrderDbSchema,UpdateOrderDbSchema
from core.decorators.db_session_handler_dec import start_db_transaction
from math import ceil
from ..models.user import Users
from models.response_models.req_res_models import SuccessResponseTypDict,BaseResponseTypDict,ErrorResponseTypDict
from core.data_formats.enums.filters_enum import OrdersFilters
from core.utils.discount_validator import validate_discount



class OrdersRepo(BaseRepoModel):
    def __init__(self,session:AsyncSession,user_role:UserRoles,cur_user_id:str):
        self.session=session
        self.user_role=user_role
        self.cur_user_id=cur_user_id
        self.orders_cols=(
            Orders.id,
            Orders.sequence_id,
            Orders.customer_id,
            Orders.product_id,
            Orders.distributor_id,
            Orders.quantity,
            Orders.total_price,
            Orders.discount,
            Orders.final_price,
            Orders.delivery_info,
            Orders.payment_status,
            Orders.invoice_status,
            Products.name.label('product_name'),
            Products.product_type,
            Products.description,
            Customers.name.label('customer_name'),
            Customers.mobile_number,
            Distributors.name.label('distributor_name'),
            Distributors.discount.label('distributor_discount'),
            Orders.invoice_number,
            Orders.invoice_date,
            Orders.purchase_type,
            Orders.renewal_type,
            Orders.unit_price,
            Orders.bill_to,
            Orders.vendor_commision
        )

    async def is_order_exists(self,customer_id:str,product_id:str):
        is_exists=(
            await self.session.execute(
                select(Orders.id)
                .where(
                    Orders.customer_id==customer_id,
                    Orders.product_id==product_id
                )
            )
        ).scalar_one_or_none()


    @start_db_transaction
    async def add(self,data:AddOrderDbSchema):
        self.session.add(Orders(**data.model_dump(mode='json')))
        # need to implement invoice generation process + email sending
        return True
    
    @start_db_transaction
    async def update(self,data:UpdateOrderDbSchema):
        data_toupdate=data.model_dump(mode='json',exclude=['product_id','customer_id','order_id'],exclude_none=True,exclude_unset=True)
        if not data_toupdate or len(data_toupdate)<1:
            return ErrorResponseTypDict(status_code=400,success=False,msg="Error : Updating Order",description="No valid fields to update provided")
        
        order_toupdate=update(Orders).where(Orders.id==data.order_id,Orders.customer_id==data.customer_id).values(
            **data_toupdate
        ).returning(Orders.id)

        is_updated=(await self.session.execute(order_toupdate)).scalar_one_or_none()
        
        # need to implement invoice generation process + email sending
        return is_updated if is_updated else ErrorResponseTypDict(status_code=400,success=False,msg="Error : Updating Order",description="Unable to update the order, may be invalid order id or no changes in data")

    @start_db_transaction    
    async def delete(self,order_id:str,customer_id:str,soft_delete:bool=True):
        ic(soft_delete)
        if soft_delete:
            order_todelete=update(Orders).where(Orders.id==order_id,Orders.customer_id==customer_id,Orders.is_deleted==False).values(
                is_deleted=True,
                deleted_at=func.now(),
                deleted_by=self.cur_user_id
            ).returning(Orders.id)

            is_deleted=(await self.session.execute(order_todelete)).scalar_one_or_none()

        else:
            if self.user_role if isinstance(self.user_role,UserRoles) else self.user_role!=UserRoles.SUPER_ADMIN.value:
                return ErrorResponseTypDict(status_code=403,success=False,msg="Error : Deleting Order",description="Only super admin can perform hard delete operation")
            
            order_todelete=delete(Orders).where(Orders.id==order_id,Orders.customer_id==customer_id).returning(Orders.id)
            is_deleted=(await self.session.execute(order_todelete)).scalar_one_or_none()
            
            # need to implement email sending "Your orders has been stoped from CRM"
        return is_deleted if is_deleted else ErrorResponseTypDict(status_code=400,success=False,msg="Error : Deleting Order",description="Unable to delete the order, may be invalid order id or order already deleted")
    
    @start_db_transaction
    async def recover(self,order_id:str,customer_id:str):
        if self.user_role if isinstance(self.user_role,UserRoles) else self.user_role!=UserRoles.SUPER_ADMIN.value:
            return ErrorResponseTypDict(status_code=403,success=False,msg="Error : Recovering Order",description="Only super admin can perform recover operation")
        
        order_torecover=update(Orders).where(Orders.id==order_id,Orders.customer_id==customer_id,Orders.is_deleted==True).values(
            is_deleted=False
        ).returning(Orders.id)
        is_recovered=(await self.session.execute(order_torecover)).scalar_one_or_none()
        return is_recovered if is_recovered else ErrorResponseTypDict(status_code=400,success=False,msg="Error : Recovering Order",description="Unable to recover the order, may order is not deleted or already recovered")


    async def get(
        self,
        cursor: int = 1,
        limit: int = 10,
        query: str = '',
        include_deleted: bool = False,
        filter: OrdersFilters | None = None
    ):
        conditions = []
        total_orders_condition=[]

        search_term = f"%{query.lower()}%"
        # cursor = (offset - 1) * limit

        # ---------------- BASE CONDITIONS ----------------
        conditions.append(
            or_(
                Orders.id.ilike(search_term),
                Orders.distributor_id.ilike(search_term),
                Products.name.ilike(search_term),
                Products.id.ilike(search_term),
                Products.product_type.ilike(search_term),
                Customers.name.ilike(search_term),
                Customers.email.ilike(search_term),
                Customers.mobile_number.ilike(search_term),
                func.cast(Orders.created_at, String).ilike(search_term),
                Orders.invoice_status.ilike(search_term),
                Orders.payment_status.ilike(search_term),
                Orders.invoice_number.ilike(search_term),
                Orders.invoice_date.ilike(search_term),
                Orders.purchase_type.ilike(search_term),
                Orders.renewal_type.ilike(search_term),
                Distributors.name.ilike(search_term),
                Orders.bill_to.ilike(search_term)
            )
        )

        # conditions.append(Orders.sequence_id > cursor)
        conditions.append(Orders.is_deleted.is_(include_deleted))

        # ---------------- FILTER LOGIC (IMPORTANT) ----------------
        if filter == OrdersFilters.PENDING_DUES:
            conditions.append(Orders.payment_status == PaymentStatus.NOT_PAID.value)
            total_orders_condition.append(Orders.payment_status == PaymentStatus.NOT_PAID.value)

        elif filter == OrdersFilters.PENDING_INVOICE:
            conditions.append(Orders.invoice_status == InvoiceStatus.INCOMPLETED.value)
            total_orders_condition.append(Orders.invoice_status == InvoiceStatus.INCOMPLETED.value)

        # ---------------- DATE FIELDS ----------------
        date_expr = func.date(func.timezone("Asia/Kolkata", Orders.created_at))
        deleted_at = func.date(func.timezone("Asia/Kolkata", Orders.deleted_at))

        cols = [*self.orders_cols]
        if include_deleted:
            cols.extend([
                Users.name.label("deleted_by"),
                deleted_at.label("deleted_at")
            ])

        queried_orders = (
            await self.session.execute(
                select(
                    *cols,
                    date_expr.label("order_created_at")
                )
                .join(Products, Products.id == Orders.product_id, isouter=True)
                .join(Customers, Customers.id == Orders.customer_id, isouter=True)
                .join(Distributors, Distributors.id == Orders.distributor_id, isouter=True)
                .join(Users, Users.id == Orders.deleted_by, isouter=True)
                .where(*conditions,Orders.sequence_id>cursor)
                .limit(limit)
                .order_by(Orders.sequence_id.asc())
            )
        ).mappings().all()


        total_orders:int=0
        total_revenue=0
        order_value=0
        pending_dues=0
        pending_invoice=0
        ic(cursor)
        if cursor==1:
            vendor_comm_amount = case(
                # WHEN vendor_commision LIKE '%'
                (
                    Orders.vendor_commision.like('%\%%'),
                    # percentage: (unit_price * quantity) * percent / 100
                    (
                        cast(func.coalesce(Orders.unit_price, 0), Numeric) *
                        cast(func.coalesce(Orders.quantity, 0), Numeric)
                    )
                    *
                    (
                        cast(func.replace(Orders.vendor_commision, '%', ''), Numeric) / 100
                    )
                ),
                # ELSE flat amount
                else_=cast(func.coalesce(Orders.vendor_commision, '0'), Numeric)
            )

            profit_expr = (
                (cast(func.coalesce(Orders.unit_price, 0), Numeric) *
                cast(func.coalesce(Orders.quantity, 0), Numeric))
                -
                vendor_comm_amount
                -
                cast(func.coalesce(Orders.final_price, 0), Numeric)
            )
            ic("iii")
            total_revenue=(await self.session.execute(
                select(func.coalesce(func.sum(profit_expr), 0))
                .where(Orders.is_deleted==False)
            )).scalar()
            ic(total_revenue)
            
            total_orders=(await self.session.execute(
                select(func.count(Orders.id))
                .where(Orders.is_deleted==False,*total_orders_condition)
            )).scalar_one_or_none()

            order_value=(await self.session.execute(
                func.sum(Orders.final_price)
            )).scalar()

            pending_invoice=(
                await self.session.execute(
                    select(
                        func.count().filter(Orders.invoice_status == InvoiceStatus.INCOMPLETED.value).label("pending_invoices")
                    ).where(Orders.is_deleted==False)
                )
            ).scalar_one_or_none()
            pending_dues=(
                await self.session.execute(
                    select(func.count().filter(Orders.payment_status == PaymentStatus.NOT_PAID.value).label("pending_dues"))
                    .where(Orders.is_deleted==False)
                )
            ).scalar_one_or_none()

        ic(total_orders,limit,total_revenue,order_value)
        ic("Hi",func.round(order_value,0))
        ic(queried_orders)

        return {
            'orders':queried_orders,
            'total_orders':total_orders,
            'total_pages':ceil(total_orders/limit),
            'total_revenue':round(total_revenue) if total_revenue else 0,
            'order_value':round(order_value,0) if order_value else 0,
            'pending_invoice':pending_invoice,
            'pending_dues':pending_dues,
            'next_cursor':queried_orders[-1]['sequence_id'] if len(queried_orders)>0 else None
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
            .join(Distributors,Distributors.id==Orders.distributor_id,isouter=True)
            .where(
                or_(
                    Orders.id.ilike(search_term),
                    Orders.distributor_id.ilike(search_term),
                    Products.name.ilike(search_term),
                    Products.id.ilike(search_term),
                    Products.product_type.ilike(search_term),
                    Customers.name.ilike(search_term),
                    Customers.email.ilike(search_term),
                    Customers.mobile_number.ilike(search_term),
                    func.cast(Orders.created_at,String).ilike(search_term),
                    Orders.invoice_status.ilike(search_term),
                    Orders.payment_status.ilike(search_term),
                    Orders.invoice_number.ilike(search_term),
                    Orders.invoice_date.ilike(search_term),
                    Orders.purchase_type.ilike(search_term),
                    Orders.renewal_type.ilike(search_term),
                    Distributors.name.ilike(search_term),
                    Orders.bill_to.ilike(search_term)
                ),
                Orders.is_deleted==False
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
            .join(Distributors,Distributors.id==Orders.distributor_id,isouter=True) 
            .where(Orders.id==order_id,Orders.is_deleted==False)
        )).mappings().one_or_none()

        return {'order':queried_orders}
        
    
    async def get_by_customer_id(self,customer_id:str,cursor:int,limit:int):
        date_expr=func.date(func.timezone("Asia/Kolkata",Orders.created_at))
        queried_orders=(await self.session.execute(
            select(
                *self.orders_cols,
                date_expr.label("order_created_at")   
            )
            .join(Products,Products.id==Orders.product_id,isouter=True)
            .join(Customers,Customers.id==Orders.customer_id,isouter=True)
            .join(Distributors,Distributors.id==Orders.distributor_id,isouter=True) 
            .where(Orders.customer_id==customer_id,Orders.sequence_id>cursor,Orders.is_deleted==False)
            .limit(limit)
        )).mappings().all()

        total_orders:int=0
        total_revenue:int=0
        highest_revenue:int=0
        if cursor==1 or cursor==0:
            profit_expr = (
                ((cast(func.coalesce(Orders.unit_price, 0), Numeric) *
                cast(func.coalesce(Orders.quantity, 0), Numeric)))
                -
                cast(func.coalesce(Orders.final_price, 0), Numeric)
            )
            total_orders=(await self.session.execute(
                select(func.count(Orders.id))
                .where(Orders.customer_id==customer_id,Orders.is_deleted==False)
            )).scalar_one_or_none()

            total_revenue=(await self.session.execute(
                select(func.coalesce(func.sum(profit_expr), 0))
                .where(Orders.customer_id==customer_id,Orders.is_deleted==False)
            )).scalar_one_or_none()

            highest_revenue=(await self.session.execute(
                select(func.max(Orders.final_price))
                .where(Orders.customer_id==customer_id,Orders.is_deleted==False)
            )).scalar()

        return {
            'orders':queried_orders,
            'total_orders':total_orders,
            'total_pages':ceil(total_orders/limit),
            'total_revenue':total_revenue,
            'highest_revenue':highest_revenue,
            'next_cursor':queried_orders[-1]['sequence_id'] if len(queried_orders)>0 else []
        }



