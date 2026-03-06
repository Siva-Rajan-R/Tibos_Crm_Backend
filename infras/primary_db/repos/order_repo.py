from typing import cast,List
from . import HTTPException,BaseRepoModel
from ..models.order import Orders,OrdersPaymentInvoiceInfo
from ..models.product import Products
from ..models.customer import Customers
from ..models.distributor import Distributors
from core.utils.uuid_generator import generate_uuid
from sqlalchemy import Numeric, select,delete,update,or_,func,String,cast,case,and_,Date,desc,text
from sqlalchemy.ext.asyncio import AsyncSession
from icecream import ic
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import literal,true
from core.data_formats.enums.user_enums import UserRoles
from core.data_formats.enums.order_enums import PaymentStatus,InvoiceStatus,PurchaseTypes,OrderFilterRevenueEnum
from schemas.db_schemas.order import AddOrderDbSchema,UpdateOrderDbSchema
from core.decorators.db_session_handler_dec import start_db_transaction
from math import ceil
from ..models.user import Users
from models.response_models.req_res_models import SuccessResponseTypDict,BaseResponseTypDict,ErrorResponseTypDict
from core.utils.discount_validator import validate_discount
from ..models.ui_id import TablesUiLId
from schemas.request_schemas.order import OrderFilterSchema
from datetime import datetime,timedelta
from core.constants import DEFAULT_ADDON_YEAR
from typing import Optional,Literal
from core.data_formats.enums.order_enums import OrderFilterDateByEnum
from ..calculations import distri_final_price,customer_final_price,profit_loss_price,customer_tot_price,distributor_tot_price,vendor_disc_price,distri_additi_price,distri_disc_price,remaining_days,last_order_delivery_date,expiry_date,distri_discount,pending_amount,total_paid_amount,customer_amount_with_gst



class OrdersRepo(BaseRepoModel):
    def __init__(self,session:AsyncSession,user_role:UserRoles,cur_user_id:str):
        self.session=session
        self.user_role=user_role
        self.cur_user_id=cur_user_id
        self.orders_cols=(
            Orders.id,
            Orders.ui_id,
            Orders.additional_discount,
            Orders.sequence_id,
            Orders.customer_id,
            Orders.product_id,
            Orders.distributor_id,
            Distributors.ui_id.label('distributor_ui_id'),
            Distributors.name.label("distributor_name"),
            Orders.discount_id,
            Orders.quantity,
            Orders.delivery_info,
            Orders.logistic_info,
            func.coalesce(
            func.jsonb_agg(
                func.jsonb_build_object(
                    "invoice_number", OrdersPaymentInvoiceInfo.invoice_number,
                    "invoice_date", OrdersPaymentInvoiceInfo.invoice_date,
                    "invoice_status", OrdersPaymentInvoiceInfo.invoice_status,
                    "payment_status", OrdersPaymentInvoiceInfo.payment_status,
                    "paid_amount", OrdersPaymentInvoiceInfo.paid_amount
                )
            ).filter(OrdersPaymentInvoiceInfo.id.isnot(None)),
            func.cast("[]", JSONB)
        ).label("status_info"),
            Products.name.label('product_name'),
            Products.product_type,
            Products.description,
            Products.price.label('product_price'),
            Customers.name.label('customer_name'),
            Customers.mobile_number,
            Distributors.name.label('distributor_name'),
            distri_discount.label('distributor_discount'),
            Orders.unit_price,
            Orders.vendor_commision,
            customer_final_price.label('customer_price'),
            distri_final_price.label('distributor_price'),
            profit_loss_price.label('profit_loss'),
            customer_tot_price.label("customer_total_price"),
            distributor_tot_price.label("distributor_total_price"),
            vendor_disc_price.label("vendor_total_price"),
            distri_disc_price.label("distri_discount_price"),
            distri_additi_price.label("distri_additi_price"),
            remaining_days.label("remaining_days"),
            last_order_delivery_date.label("last_order_date"),
            pending_amount.label("pending_amount"),
            total_paid_amount.label("total_paid_amount"),
            customer_amount_with_gst.label('customer_amount_with_gst'),
            func.date(expiry_date).label("last_order_expiry_date")

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

        return is_exists


    @start_db_transaction
    async def add(self,data:AddOrderDbSchema):
        self.session.add(Orders(**data.model_dump(mode='json',exclude=['lui_id','status_info'])))
        invoicetoadd=data.model_dump(mode='json')
        invoicetoadd_bulk=[]
        for status in invoicetoadd['status_info']:
            invoicetoadd_bulk.append(OrdersPaymentInvoiceInfo(**status,order_id=data.id))
        
        self.session.add_all(invoicetoadd_bulk)
        await self.session.execute(update(TablesUiLId).where(TablesUiLId.id=="1").values(order_luiid=data.ui_id))
        # need to implement invoice generation process + email sending
        return True
    
    @start_db_transaction
    async def add_bulk(self,datas:List[Orders],status_datas:List[OrdersPaymentInvoiceInfo],lui_id:str):
        if not datas:
            return True

        with self.session.no_autoflush:

            self.session.add_all(datas)

            await self.session.flush()

            self.session.add_all(status_datas)

        await self.session.execute(
            update(TablesUiLId)
            .where(TablesUiLId.id == "1")
            .values(order_luiid=lui_id)
        )

        return True
    
    @start_db_transaction
    async def update(self,data:UpdateOrderDbSchema):
        data_toupdate=data.model_dump(mode='json',exclude=['product_id','customer_id','order_id','status_info'],exclude_none=True,exclude_unset=True)
        if not data_toupdate or len(data_toupdate)<1:
            return ErrorResponseTypDict(status_code=400,success=False,msg="Error : Updating Order",description="No valid fields to update provided")
        
        invoicetoadd=data.model_dump(mode='json')
        invoicetoadd_bulk=[]
        await self.session.execute(delete(OrdersPaymentInvoiceInfo).where(OrdersPaymentInvoiceInfo.order_id==data.order_id))
        for status in invoicetoadd['status_info']:
            invoicetoadd_bulk.append(OrdersPaymentInvoiceInfo(**status,order_id=data.order_id))
        
        self.session.add_all(invoicetoadd_bulk)

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
        filter: Optional[OrderFilterSchema]=OrderFilterSchema(),
        cursor: int = 1,
        limit: int = 10,
        query: str = '',
        include_deleted: bool = False,
    ):

        
        conditions = []
        total_orders_condition=[]
        filters=[]
        filter_mapper={
            'payment_status':OrdersPaymentInvoiceInfo.payment_status,
            'invoice_status':OrdersPaymentInvoiceInfo.invoice_status,
            'purchase_type':Orders.logistic_info['purchase_type'].astext,
            'renewal_type':Orders.logistic_info['renewal_type'].astext,
            'distributor_type':Orders.logistic_info['distributor_type'].astext
        }
        cursor=0 if cursor==1 else cursor
        search_term = f"%{query.lower()}%"
        # cursor = (offset - 1) * limit

        # ---------------- BASE CONDITIONS ----------------
        conditions.append(
            or_(
                Orders.id.ilike(search_term),
                Orders.ui_id.ilike(search_term),
                Orders.distributor_id.ilike(search_term),
                Products.name.ilike(search_term),
                Products.id.ilike(search_term),
                Products.product_type.ilike(search_term),
                Customers.name.ilike(search_term),
                Customers.email.ilike(search_term),
                Customers.mobile_number.ilike(search_term),
                Orders.logistic_info['purchase_type'].astext.ilike(search_term),
                Orders.logistic_info['renewal_type'].astext.ilike(search_term),
                Distributors.name.ilike(search_term),
                Orders.logistic_info['bill_to'].astext.ilike(search_term),
                Orders.logistic_info['distributor_type'].astext.ilike(search_term)
            )
        )

        # conditions.append(Orders.sequence_id > cursor)
        conditions.append(Orders.is_deleted.is_(include_deleted))
        # ---------------- DATE FIELDS ----------------
        date_expr = func.date(func.timezone("Asia/Kolkata", Orders.created_at))
        deleted_at = func.date(func.timezone("Asia/Kolkata", Orders.deleted_at))
        ic("Hello 1")
        cols = [*self.orders_cols]
        if include_deleted:
            cols.extend([
                Users.name.label("deleted_by"),
                deleted_at.label("deleted_at")
            ])

        ic("hello 2")
        for key,value in filter.model_dump(mode='json').items():
            if value is not None and key!="date_filter" and key!="revenue_type":
                filters.append(filter_mapper[key]==value)
        

        ic(filters)
        orders_toquery = (
                select(
                    *cols,
                    date_expr.label("order_created_at")
                )
                .join(OrdersPaymentInvoiceInfo,OrdersPaymentInvoiceInfo.order_id==Orders.id,isouter=True)
                .join(Products, Products.id == Orders.product_id, isouter=True)
                .join(Customers, Customers.id == Orders.customer_id, isouter=True)
                .join(Distributors, Distributors.id == Orders.distributor_id, isouter=True)
                .join(Users, Users.id == Orders.deleted_by, isouter=True)
                .where(
                    *conditions,
                    *filters,
                    Orders.sequence_id>cursor
                )
                .limit(limit)
                .order_by(Orders.sequence_id.asc())
                .group_by(
                    Orders.id,
                    OrdersPaymentInvoiceInfo.order_id,
                    Products.id,
                    Users.id,
                    Customers.id,
                    Distributors.id
                )

        )

        ic(filter.date_filter)
        date_by = filter.date_filter.get("by").value if filter.date_filter.get("by") else None
        date_tofilter = None

        if date_by == OrderFilterDateByEnum.REQUESTED_DATE.value:
            date_tofilter = cast(Orders.delivery_info["requested_date"].astext,Date)

        elif date_by == OrderFilterDateByEnum.ACTIVATION_DATE.value: 
            date_tofilter = cast(Orders.delivery_info["delivery_date"].astext,Date)
            ic("iam in activation date ",date_tofilter)

        elif date_by == OrderFilterDateByEnum.CREATED_DATE.value:
            date_tofilter = cast(Orders.created_at,Date)
        ic(date_tofilter)

        date_filter_condition=None
        revenue_filter_condition=None

        if date_tofilter is not None:
            final_date = cast(date_tofilter, Date)
            from_date = filter.date_filter.get("from_date")
            to_date = filter.date_filter.get("to_date")
            ic(from_date,to_date,final_date)
            orders_toquery = orders_toquery.where(
                and_(
                    final_date >= from_date,
                    final_date <= to_date
                )
            )

            date_filter_condition=and_(
                final_date >= from_date,
                final_date <= to_date
            )
        ic(filter)
        ic(type(filter))
        ic()
       
        if getattr(filter,'revenue_type',None):
            revenue=filter.revenue_type.value if isinstance(filter.revenue_type,OrderFilterRevenueEnum) else filter.revenue_type
            if revenue==OrderFilterRevenueEnum.PROFIT.value:
                revenue_filter_condition=and_(
                    profit_loss_price>0
                )

                orders_toquery=orders_toquery.where(
                    and_(
                        profit_loss_price>0
                    )
                )

            elif revenue==OrderFilterRevenueEnum.LOSS.value:
                revenue_filter_condition=and_(
                    profit_loss_price<0
                )

                orders_toquery=orders_toquery.where(
                    and_(
                        profit_loss_price<0
                    )
                )
        
        queried_orders=(await self.session.execute(orders_toquery)).mappings().all()
        total_orders:int=0
        total_revenue=0
        order_value=0
        pending_dues=0
        pending_amounts=0
        pending_invoice=0
        ic(cursor)
        if cursor==0:
            ic("iii")
            total_revenue=(await self.session.execute(
                select(func.coalesce(func.sum(profit_loss_price), 0))
                .join(Products, Products.id == Orders.product_id, isouter=True)
                .join(Customers, Customers.id == Orders.customer_id, isouter=True)
                .join(Distributors, Distributors.id == Orders.distributor_id, isouter=True)
                .join(Users, Users.id == Orders.deleted_by, isouter=True)
                .where(*conditions,*filters,Orders.is_deleted==False)
                .where(date_filter_condition if date_filter_condition is not None else true())
                .where(revenue_filter_condition if revenue_filter_condition is not None else true())
            )).scalar()
            ic(total_revenue)
            
            total_orders=(await self.session.execute(
                select(func.count(Orders.id))
                .join(Products, Products.id == Orders.product_id, isouter=True)
                .join(Customers, Customers.id == Orders.customer_id, isouter=True)
                .join(Distributors, Distributors.id == Orders.distributor_id, isouter=True)
                .join(Users, Users.id == Orders.deleted_by, isouter=True)
                .where(*conditions,*filters,Orders.is_deleted==False,*total_orders_condition)
                .where(date_filter_condition if date_filter_condition is not None else true())
                .where(revenue_filter_condition if revenue_filter_condition is not None else true())

            )).scalar_one_or_none()

            order_value=(await self.session.execute(
                select(func.sum(customer_final_price))
                .join(Products, Products.id == Orders.product_id, isouter=True)
                .join(Customers, Customers.id == Orders.customer_id, isouter=True)
                .join(Distributors, Distributors.id == Orders.distributor_id, isouter=True)
                .join(Users, Users.id == Orders.deleted_by, isouter=True)
                .where(*conditions,*filters,Orders.is_deleted==False)
                .where(date_filter_condition if date_filter_condition is not None else true())
                .where(revenue_filter_condition if revenue_filter_condition is not None else true())
            )).scalar()

            pending_invoice=(
                await self.session.execute(
                    select(
                        func.count().filter(OrdersPaymentInvoiceInfo.invoice_status == InvoiceStatus.INCOMPLETED.value).label("pending_invoices")
                    )
                    .select_from(Orders)
                    .join(OrdersPaymentInvoiceInfo,OrdersPaymentInvoiceInfo.order_id==Orders.id,isouter=True)
                    .join(Products, Products.id == Orders.product_id, isouter=True)
                    .join(Customers, Customers.id == Orders.customer_id, isouter=True)
                    .join(Distributors, Distributors.id == Orders.distributor_id, isouter=True)
                    .join(Users, Users.id == Orders.deleted_by, isouter=True)
                    .where(*conditions,*filters,Orders.is_deleted==False)
                    .where(date_filter_condition if date_filter_condition is not None else true())
                    .where(revenue_filter_condition if revenue_filter_condition is not None else true())
                    
                )
            ).scalar_one_or_none()
            pending_dues=(
                await self.session.execute(
                    select(func.count().filter(and_(OrdersPaymentInvoiceInfo.payment_status != PaymentStatus.PAID.value,OrdersPaymentInvoiceInfo.payment_status != PaymentStatus.FULL_PAYMENT_RECEIVED.value)).label("pending_dues"))
                    .select_from(Orders)
                    .join(OrdersPaymentInvoiceInfo,OrdersPaymentInvoiceInfo.order_id==Orders.id,isouter=True)
                    .join(Products, Products.id == Orders.product_id, isouter=True)
                    .join(Customers, Customers.id == Orders.customer_id, isouter=True)
                    .join(Distributors, Distributors.id == Orders.distributor_id, isouter=True)
                    .join(Users, Users.id == Orders.deleted_by, isouter=True)
                    .where(*conditions,*filters,Orders.is_deleted==False)
                    .where(date_filter_condition if date_filter_condition is not None else true())
                    .where(revenue_filter_condition if revenue_filter_condition is not None else true())
                    
                )
            ).scalar_one_or_none()

            payment_subq = (
                select(
                    OrdersPaymentInvoiceInfo.order_id,
                    func.sum(func.coalesce(OrdersPaymentInvoiceInfo.paid_amount, 0)).label("paid_total")
                )
                .group_by(OrdersPaymentInvoiceInfo.order_id)
                .subquery()
            )

            customer_price = (Orders.unit_price * Orders.quantity)

            query = (
                select(
                    func.sum(
                        func.round(customer_price * 1.18) -
                        func.coalesce(payment_subq.c.paid_total, 0)
                    ).label("total_due")
                ).outerjoin(
                    payment_subq, payment_subq.c.order_id == Orders.id
                )
                .join(OrdersPaymentInvoiceInfo,OrdersPaymentInvoiceInfo.order_id==Orders.id,isouter=True)
                .join(Products, Products.id == Orders.product_id, isouter=True)
                .join(Customers, Customers.id == Orders.customer_id, isouter=True)
                .join(Distributors, Distributors.id == Orders.distributor_id, isouter=True)
                .join(Users, Users.id == Orders.deleted_by, isouter=True)
                .where(*conditions, *filters, Orders.is_deleted == False)
                .where(date_filter_condition if date_filter_condition is not None else true())
                .where(revenue_filter_condition if revenue_filter_condition is not None else true())
                .where(and_(OrdersPaymentInvoiceInfo.payment_status != PaymentStatus.PAID.value,OrdersPaymentInvoiceInfo.payment_status != PaymentStatus.FULL_PAYMENT_RECEIVED.value))
            )

            result = await self.session.execute(query)
            total_due = result.scalar()
        #     pending_amounts = (
        #     await self.session.execute(
        #         select(
        #             func.sum(
        #                 func.round(func.coalesce(Orders.unit_price * Orders.quantity, 0) * 1.18) - 
        #                 func.round(func.coalesce(paid_per_order.c.total_paid, 0))
        #             ).label("total")
        #         )
        #         .select_from(Orders)
        #         .join(Products, Products.id == Orders.product_id, isouter=True)
        #         .outerjoin(paid_per_order, paid_per_order.c.order_id == Orders.id)
        #         .join(Customers, Customers.id == Orders.customer_id, isouter=True)
        #         .join(Distributors, Distributors.id == Orders.distributor_id, isouter=True)
        #         .join(Users, Users.id == Orders.deleted_by, isouter=True)
        #         .where(*conditions, *filters, Orders.is_deleted == False)
        #         .where(date_filter_condition if date_filter_condition is not None else true())
        #         .where(revenue_filter_condition if revenue_filter_condition is not None else true())
        #     )
        # ).scalar_one_or_none()

        ic(total_orders,limit,total_revenue,order_value,total_due)
        ic("Hi",func.round(order_value,0))

        return {
            'orders':queried_orders,
            'total_orders':total_orders,
            'total_pages':ceil(total_orders/limit),
            'total_revenue':round(total_revenue) if total_revenue else 0,
            'order_value':round(order_value,0) if order_value else 0,
            'pending_invoice':pending_invoice,
            'pending_dues':pending_dues,
            'pending_amounts':total_due,
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
            .join(OrdersPaymentInvoiceInfo,OrdersPaymentInvoiceInfo.order_id==Orders.id,isouter=True)
            .join(Products, Products.id == Orders.product_id, isouter=True)
            .join(Customers, Customers.id == Orders.customer_id, isouter=True)
            .join(Distributors, Distributors.id == Orders.distributor_id, isouter=True)
            .join(Users, Users.id == Orders.deleted_by, isouter=True)
            .where(
                or_(
                    Orders.id.ilike(search_term),
                    Orders.ui_id.ilike(search_term),
                    Orders.distributor_id.ilike(search_term),
                    Products.name.ilike(search_term),
                    Products.id.ilike(search_term),
                    Products.product_type.ilike(search_term),
                    Customers.name.ilike(search_term),
                    Customers.email.ilike(search_term),
                    Customers.mobile_number.ilike(search_term),
                    func.cast(Orders.created_at, String).ilike(search_term),
                    Orders.logistic_info['purchase_type'].astext.ilike(search_term),
                    Orders.logistic_info['renewal_type'].astext.ilike(search_term),
                    Distributors.name.ilike(search_term),
                    Orders.logistic_info['bill_to'].astext.ilike(search_term),
                    Orders.logistic_info['distributor_type'].astext.ilike(search_term)
                ),
                Orders.is_deleted==False
            )
            .group_by(
                    Orders.id,
                    OrdersPaymentInvoiceInfo.order_id,
                    Products.id,
                    Customers.id,
                    Distributors.id
                )
            .limit(5)
        )).mappings().all()

        return {'orders':queried_orders}

        
    async def get_by_id(self,order_id:str):
        date_expr=func.date(func.timezone("Asia/Kolkata",Orders.created_at))
        queried_orders=(await self.session.execute(
            select(
                *self.orders_cols,
                date_expr.label("order_created_at"), 
                Customers.email.label('customer_email')
            )
            .join(OrdersPaymentInvoiceInfo,OrdersPaymentInvoiceInfo.order_id==Orders.id,isouter=True)
            .join(Products,Products.id==Orders.product_id,isouter=True)
            .join(Customers,Customers.id==Orders.customer_id,isouter=True)
            .join(Distributors,Distributors.id==Orders.distributor_id,isouter=True) 
            .where(or_(Orders.id==order_id,Orders.ui_id==order_id),Orders.is_deleted==False)
            .group_by(
                Orders.id,
                OrdersPaymentInvoiceInfo.order_id,
                Products.id,
                Customers.id,
                Distributors.id
            )
        )).mappings().one_or_none()

        return {'order':queried_orders}
        
    
    async def get_by_customer_id(self,customer_id:str,cursor:int,limit:int):
        date_expr=func.date(func.timezone("Asia/Kolkata",Orders.created_at))
        cursor=0 if cursor==1 else cursor
        queried_orders=(await self.session.execute(
            select(
                *self.orders_cols,
                date_expr.label("order_created_at")   
            )
            .join(Products,Products.id==Orders.product_id,isouter=True)
            .join(Customers,Customers.id==Orders.customer_id,isouter=True)
            .join(Distributors,Distributors.id==Orders.distributor_id,isouter=True) 
            .where(Orders.customer_id==customer_id,Orders.sequence_id>cursor,Orders.is_deleted==False)
            .group_by(
                    Orders.id,
                    OrdersPaymentInvoiceInfo.order_id,
                    Products.id,
                    Customers.id,
                    Distributors.id
                )
            .limit(limit)
        )).mappings().all()

        total_orders:int=0
        total_revenue=0
        order_value=0
        pending_dues=0
        pending_invoice=0
        ic(cursor)
        if cursor==0:
            total_revenue=(await self.session.execute(
                select(func.coalesce(func.sum(profit_loss_price), 0))
                .join(Products,Products.id==Orders.product_id,isouter=True)
                .join(Customers,Customers.id==Orders.customer_id,isouter=True)
                .join(Distributors,Distributors.id==Orders.distributor_id,isouter=True)
                .where(Orders.is_deleted==False,Orders.customer_id==customer_id)
            )).scalar()
            ic(total_revenue)
            
            total_orders=(await self.session.execute(
                select(func.count(Orders.id))
                .join(Products,Products.id==Orders.product_id,isouter=True)
                .join(Customers,Customers.id==Orders.customer_id,isouter=True)
                .join(Distributors,Distributors.id==Orders.distributor_id,isouter=True)
                .where(Orders.is_deleted==False,Orders.customer_id==customer_id)
            )).scalar_one_or_none()

            order_value=(await self.session.execute(
                select(func.sum(customer_final_price))
                .join(Products,Products.id==Orders.product_id,isouter=True)
                .join(Customers,Customers.id==Orders.customer_id,isouter=True)
                .join(Distributors,Distributors.id==Orders.distributor_id,isouter=True)
                .where(Orders.is_deleted==False,Orders.customer_id==customer_id)
                
            )).scalar()

            pending_invoice=(
                await self.session.execute(
                    select(
                        func.count().filter(OrdersPaymentInvoiceInfo.invoice_status == InvoiceStatus.INCOMPLETED.value).label("pending_invoices")
                    )
                    .join(Products,Products.id==Orders.product_id,isouter=True)
                    .join(Customers,Customers.id==Orders.customer_id,isouter=True)
                    .join(Distributors,Distributors.id==Orders.distributor_id,isouter=True)
                    .where(Orders.is_deleted==False,Orders.customer_id==customer_id)
                )
            ).scalar_one_or_none()
            pending_dues=(
                await self.session.execute(
                    select(func.count().filter(OrdersPaymentInvoiceInfo.payment_status == PaymentStatus.NOT_PAID.value).label("pending_dues"))
                    .join(Products,Products.id==Orders.product_id,isouter=True)
                    .join(Customers,Customers.id==Orders.customer_id,isouter=True)
                    .join(Distributors,Distributors.id==Orders.distributor_id,isouter=True)
                    .where(Orders.is_deleted==False,Orders.customer_id==customer_id)
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
    

    async def get_last_order(self,customer_id:str,product_id:str):
        date_expr=cast(
            Orders.delivery_info['delivery_date'].astext,
            Date
        )

        last_ord_stmt=(
            select(
                Orders.unit_price,
                Orders.logistic_info,
                Orders.delivery_info,
                date_expr.label("last_date")
            )
            .where(
                Orders.customer_id==customer_id,
                Orders.product_id==product_id,
                Orders.is_deleted==False,
                Orders.logistic_info['purchase_type'].astext!=PurchaseTypes.EXISTING_ADD_ON.value
            )
            .order_by(desc(date_expr))
            .limit(1)
        )
        
        last_ord=(await self.session.execute(last_ord_stmt)).mappings().one_or_none()
        return {'last_order':{**last_ord,'expiry_date':last_ord['last_date']+timedelta(days=DEFAULT_ADDON_YEAR+1)}if last_ord else last_ord}
    




