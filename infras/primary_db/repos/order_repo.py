from typing import cast,List
import io
import pandas as pd
from . import HTTPException,BaseRepoModel
from ..models.order import Orders,OrdersPaymentInvoiceInfo
from ..models.product import Products
from ..models.customer import Customers
from ..models.distributor import Distributors
from core.utils.uuid_generator import generate_uuid
from sqlalchemy import Numeric, select,delete,update,or_,func,String,cast,case,and_,Date,desc,text,exists
from sqlalchemy.ext.asyncio import AsyncSession
from icecream import ic
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import literal,true
from core.data_formats.enums.user_enums import UserRoles
from core.data_formats.enums.order_enums import PaymentStatus,InvoiceStatus,PurchaseTypes,OrderFilterRevenueEnum,ActivationStatusEnum
from schemas.db_schemas.order import AddOrderDbSchema,UpdateOrderDbSchema,OrderBulkDeleteDbSchema
from core.decorators.db_session_handler_dec import start_db_transaction
from math import ceil
from ..models.user import Users
from models.response_models.req_res_models import SuccessResponseTypDict,BaseResponseTypDict,ErrorResponseTypDict
from core.utils.discount_validator import validate_discount
from ..models.ui_id import TablesUiLId
from schemas.request_schemas.order import OrderFilterSchema
from datetime import datetime, timedelta, date
from core.constants import DEFAULT_ADDON_YEAR
from typing import Optional,Literal
from core.data_formats.enums.order_enums import OrderFilterDateByEnum
from ..calculations import distri_final_price,customer_final_price,customer_final_price_inc_gst,profit_loss_price,customer_tot_price,distributor_tot_price,vendor_disc_price,distri_additi_price,distri_disc_price,remaining_days,last_order_delivery_date,expiry_date,distri_discount,pending_amount,total_paid_amount,customer_amount_with_gst



class OrdersRepo(BaseRepoModel):
    def __init__(self,session:AsyncSession,user_role:UserRoles,cur_user_id:str):
        self.session=session
        self.user_role=user_role
        self.cur_user_id=cur_user_id
        self.subquery=(
                select(
                    OrdersPaymentInvoiceInfo.order_id,

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

                    func.coalesce(
                        func.sum(OrdersPaymentInvoiceInfo.paid_amount), 0
                    ).label("total_paid_amount"),
                    


                )
                .group_by(OrdersPaymentInvoiceInfo.order_id)
                .subquery()
            )
        self.orders_cols=(
            Orders.id,
            Orders.ui_id,
            Orders.additional_discount,
            Orders.sequence_id,
            Orders.customer_id,
            Orders.product_id,
            Orders.distributor_id,
            Orders.activated,
            Orders.additional_price,
            Distributors.ui_id.label('distributor_ui_id'),
            Distributors.name.label("distributor_name"),
            Orders.discount_id,
            Orders.quantity,
            Orders.delivery_info,
            Orders.logistic_info,
            Products.ui_id.label("product_ui_id"),
            Products.name.label('product_name'),
            Products.product_type.label("product_type"),
            Products.product_type,
            Products.description,
            Products.price.label('product_price'),
            Customers.name.label('customer_name'),
            Customers.ui_id.label("customer_ui_id"),
            Customers.mobile_number,
            Customers.owner.label("owner_name"),
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
            customer_amount_with_gst.label('customer_amount_with_gst'),
            func.date(expiry_date).label("last_order_expiry_date"),
            self.subquery.c.status_info,
            self.subquery.c.total_paid_amount,

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
    async def delete_bulk(self,data:OrderBulkDeleteDbSchema,soft_delete:bool=True):
        ic(soft_delete)
        if soft_delete:
            for order_id in data.order_ids:
                order_todelete=update(Orders).where(Orders.id==order_id,Orders.is_deleted==False).values(
                    is_deleted=True,
                    deleted_at=func.now(),
                    deleted_by=self.cur_user_id
                ).returning(Orders.id)

                is_deleted=(await self.session.execute(order_todelete)).scalar_one_or_none()
        else:
            if self.user_role if isinstance(self.user_role,UserRoles) else self.user_role!=UserRoles.SUPER_ADMIN.value:
                return ErrorResponseTypDict(status_code=403,success=False,msg="Error : Deleting Order",description="Only super admin can perform hard delete operation")
            
            for order_id in data.order_ids:
                order_todelete=delete(Orders).where(Orders.id==order_id).returning(Orders.id)
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
        active:bool=False,
        filter: Optional[OrderFilterSchema]=OrderFilterSchema(),
        cursor: int = 1,
        limit: int = 10,
        query: str = '',
        include_deleted: bool = False,
        in_search:List=[]
    ):

        ic(filter)
        conditions = []
        total_orders_condition=[]
        filters=[]
        filter_mapper={
            'activation_status':Orders.activated,
            'distributor_id':Distributors.id,
            'payment_status':OrdersPaymentInvoiceInfo.payment_status,
            'invoice_status':OrdersPaymentInvoiceInfo.invoice_status,
            'purchase_type':Orders.logistic_info['purchase_type'].astext,
            'renewal_type':Orders.logistic_info['renewal_type'].astext,
            'distributor_type':Orders.logistic_info['distributor_type'].astext,
            'customer_id':Orders.customer_id,
            'distributor_id':Orders.distributor_id,
            'product_id':Orders.product_id,
            'owner_name':Customers.owner,
            'product_type':Products.product_type
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
                Distributors.ui_id.ilike(search_term),
                Products.name.ilike(search_term),
                Products.id.ilike(search_term),
                Products.ui_id.ilike(search_term),
                Products.product_type.ilike(search_term),
                Customers.name.ilike(search_term),
                Customers.email.ilike(search_term),
                Customers.mobile_number.ilike(search_term),
                Orders.logistic_info['purchase_type'].astext.ilike(search_term),
                Orders.logistic_info['renewal_type'].astext.ilike(search_term),
                Distributors.name.ilike(search_term),
                Orders.logistic_info['bill_to'].astext.ilike(search_term),
                Orders.logistic_info['distributor_type'].astext.ilike(search_term),
                exists().where(
                    and_(
                        OrdersPaymentInvoiceInfo.order_id == Orders.id,
                        OrdersPaymentInvoiceInfo.invoice_number.ilike(search_term)
                    )
                )
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
            if value is None:
                continue

            if key == "payment_status":
                filters.append(
                    exists().where(
                        and_(
                            OrdersPaymentInvoiceInfo.order_id == Orders.id,
                            OrdersPaymentInvoiceInfo.payment_status == value,
                            OrdersPaymentInvoiceInfo.invoice_status == InvoiceStatus.COMPLETED.value
                        )
                    )
                )

            elif key == "invoice_status":
                filters.append(
                    exists().where(
                        and_(
                            OrdersPaymentInvoiceInfo.order_id == Orders.id,
                            OrdersPaymentInvoiceInfo.invoice_status == value
                        )
                    )
                )

            elif key != "date_filter" and key != "revenue_type":
                filters.append(filter_mapper[key] == value)
                

        ic(filters)
        orders_toquery = (
            select(
                *cols,
                date_expr.label("order_created_at")
            )
            .join(self.subquery, self.subquery.c.order_id == Orders.id, isouter=True)
            .join(Products,Products.id==Orders.product_id,isouter=True)
            .join(Customers,Customers.id==Orders.customer_id,isouter=True)
            .join(Distributors,Distributors.id==Orders.distributor_id,isouter=True)
            # .join(OrdersPaymentInvoiceInfo, OrdersPaymentInvoiceInfo.order_id == Orders.id,isouter=True)
            .where(
                *conditions,
                *filters,
                Orders.sequence_id>cursor
            )
            .limit(limit)
            .order_by(Orders.sequence_id.asc())

        )

        ic(filter.date_filter)
        date_by = filter.date_filter.get("by").value if filter.date_filter.get("by") else None
        date_tofilter = None

        active_condition = None
        if active:
            ic("Inside the active")
            delivery_date = cast(Orders.delivery_info["delivery_date"].astext, Date)
            active_condition = and_(
                delivery_date >= func.current_date() - text("INTERVAL '365 days'"),
                Orders.activated.is_(True)
            )


        if active_condition is not None:
            orders_toquery = orders_toquery.where(active_condition)

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
        if in_search and len(in_search)>0:
            orders_toquery=orders_toquery.where(Orders.id.in_(in_search))
            
        queried_orders=(await self.session.execute(orders_toquery)).mappings().all()
        orders_infos={}
        purchase_stats=[]
        pending_amounts=0
        ic(cursor)


        if cursor==0:
            
            payment_subq = (
                select(
                    OrdersPaymentInvoiceInfo.order_id,
                    func.sum(func.coalesce(OrdersPaymentInvoiceInfo.paid_amount, 0)).label("paid_total")
                )
                .group_by(OrdersPaymentInvoiceInfo.order_id)
                .subquery()
            )

            payment_cust_price=case(
                (
                    func.coalesce(payment_subq.c.paid_total,0)>(customer_final_price*1.18),
                    0
                ),
                else_=(customer_final_price*1.18)
            )


            

            invoice_stats_subq = (
                select(
                    OrdersPaymentInvoiceInfo.order_id,
                    func.count().label("total_invoices"),

                    func.count().filter(
                        OrdersPaymentInvoiceInfo.invoice_status == InvoiceStatus.INCOMPLETED.value
                    ).label("pending_invoice"),

                    func.count().filter(
                        and_(
                            OrdersPaymentInvoiceInfo.invoice_status == InvoiceStatus.COMPLETED.value,
                            OrdersPaymentInvoiceInfo.payment_status != PaymentStatus.PAID.value,
                            OrdersPaymentInvoiceInfo.payment_status != PaymentStatus.FULL_PAYMENT_RECEIVED.value
                        )
                    ).label("completed_invoices_count"),
                    func.sum(func.coalesce(OrdersPaymentInvoiceInfo.paid_amount, 0)).filter(
                        and_(
                            OrdersPaymentInvoiceInfo.invoice_status == InvoiceStatus.COMPLETED.value,
                            OrdersPaymentInvoiceInfo.payment_status != PaymentStatus.PAID.value,
                            OrdersPaymentInvoiceInfo.payment_status != PaymentStatus.FULL_PAYMENT_RECEIVED.value
                        )
                    ).label("completed_paid_total"),

                    func.count().filter(
                        and_(
                            OrdersPaymentInvoiceInfo.payment_status == PaymentStatus.TDS_PENDING.value,
                            OrdersPaymentInvoiceInfo.invoice_status == InvoiceStatus.COMPLETED.value
                        )
                    ).label("tds_pendings"),
                    func.sum(func.coalesce(OrdersPaymentInvoiceInfo.paid_amount, 0)).filter(
                        and_(
                            OrdersPaymentInvoiceInfo.payment_status == PaymentStatus.TDS_PENDING.value,
                            OrdersPaymentInvoiceInfo.invoice_status == InvoiceStatus.COMPLETED.value
                        )
                    ).label("tds_paid_sum"),

                    func.count().filter(
                        and_(
                            OrdersPaymentInvoiceInfo.payment_status == PaymentStatus.NOT_PAID.value,
                            OrdersPaymentInvoiceInfo.invoice_status == InvoiceStatus.COMPLETED.value
                        )
                    ).label("not_paid_pendings"),
                    func.sum(func.coalesce(OrdersPaymentInvoiceInfo.paid_amount, 0)).filter(
                        and_(
                            OrdersPaymentInvoiceInfo.payment_status == PaymentStatus.NOT_PAID.value,
                            OrdersPaymentInvoiceInfo.invoice_status == InvoiceStatus.COMPLETED.value
                        )
                    ).label("not_paid_paid_sum"),

                    func.count().filter(
                        and_(
                            OrdersPaymentInvoiceInfo.payment_status == PaymentStatus.GST_PENDING.value,
                            OrdersPaymentInvoiceInfo.invoice_status == InvoiceStatus.COMPLETED.value
                        )
                    ).label("gst_pendings"),
                    func.sum(func.coalesce(OrdersPaymentInvoiceInfo.paid_amount, 0)).filter(
                        and_(
                            OrdersPaymentInvoiceInfo.payment_status == PaymentStatus.GST_PENDING.value,
                            OrdersPaymentInvoiceInfo.invoice_status == InvoiceStatus.COMPLETED.value
                        )
                    ).label("gst_paid_sum"),

                    func.count().filter(
                        and_(
                            OrdersPaymentInvoiceInfo.payment_status == PaymentStatus.HALF_PAYMENT_RECEIVED.value,
                            OrdersPaymentInvoiceInfo.invoice_status == InvoiceStatus.COMPLETED.value
                        )
                    ).label("half_pendings"),
                    func.sum(func.coalesce(OrdersPaymentInvoiceInfo.paid_amount, 0)).filter(
                        and_(
                            OrdersPaymentInvoiceInfo.payment_status == PaymentStatus.HALF_PAYMENT_RECEIVED.value,
                            OrdersPaymentInvoiceInfo.invoice_status == InvoiceStatus.COMPLETED.value
                        )
                    ).label("half_paid_sum"),

                    func.count().filter(
                        and_(
                            OrdersPaymentInvoiceInfo.payment_status == PaymentStatus.SHORT_PAYMENT_RECEIVED.value,
                            OrdersPaymentInvoiceInfo.invoice_status == InvoiceStatus.COMPLETED.value
                        )
                    ).label("short_pendings"),
                    func.sum(func.coalesce(OrdersPaymentInvoiceInfo.paid_amount, 0)).filter(
                        and_(
                            OrdersPaymentInvoiceInfo.payment_status == PaymentStatus.SHORT_PAYMENT_RECEIVED.value,
                            OrdersPaymentInvoiceInfo.invoice_status == InvoiceStatus.COMPLETED.value
                        )
                    ).label("short_paid_sum"),
                )
                .group_by(OrdersPaymentInvoiceInfo.order_id)
                .subquery()
            )

            # pending_amt_status=[
            #     s.value for s in PaymentStatus
            #     if s not in {PaymentStatus.PAID, PaymentStatus.FULL_PAYMENT_RECEIVED}
            # ]
            # pending_amount_calc=func.abs(func.round(payment_cust_price) - func.coalesce(payment_subq.c.paid_total, 0))
            

            customer_amount_with_gst = func.round(customer_final_price * 1.18)
            expected_invoice_amount = customer_amount_with_gst / func.nullif(invoice_stats_subq.c.total_invoices, 0)

            pending_amount_expr = func.round(
                func.coalesce(invoice_stats_subq.c.completed_invoices_count, 0) * expected_invoice_amount - 
                func.coalesce(invoice_stats_subq.c.completed_paid_total, 0)
            )

            pending_amount_filtered = case(
                (
                    (
                        func.coalesce(invoice_stats_subq.c.not_paid_pendings, 0) +
                        func.coalesce(invoice_stats_subq.c.tds_pendings, 0) +
                        func.coalesce(invoice_stats_subq.c.gst_pendings, 0) +
                        func.coalesce(invoice_stats_subq.c.half_pendings, 0) +
                        func.coalesce(invoice_stats_subq.c.short_pendings, 0)
                    ) > 0,
                    pending_amount_expr
                ),
                else_=0
            )


            payment_status_filter = filter.payment_status
            if hasattr(payment_status_filter, "value"):
                payment_status_filter = payment_status_filter.value

            not_paid_amount_raw = func.round(
                func.coalesce(invoice_stats_subq.c.not_paid_pendings, 0) * expected_invoice_amount - 
                func.coalesce(invoice_stats_subq.c.not_paid_paid_sum, 0)
            )

            gst_pending_amount_raw = func.round(
                func.coalesce(invoice_stats_subq.c.gst_pendings, 0) * expected_invoice_amount - 
                func.coalesce(invoice_stats_subq.c.gst_paid_sum, 0)
            )

            half_pending_amount_raw = func.round(
                func.coalesce(invoice_stats_subq.c.half_pendings, 0) * expected_invoice_amount - 
                func.coalesce(invoice_stats_subq.c.half_paid_sum, 0)
            )

            short_pending_amount_raw = func.round(
                func.coalesce(invoice_stats_subq.c.short_pendings, 0) * expected_invoice_amount - 
                func.coalesce(invoice_stats_subq.c.short_paid_sum, 0)
            )

            tds_pending_amount_raw = func.round(
                func.coalesce(invoice_stats_subq.c.tds_pendings, 0) * expected_invoice_amount - 
                func.coalesce(invoice_stats_subq.c.tds_paid_sum, 0)
            )

            not_paid_amount = case((or_(payment_status_filter == None, payment_status_filter == PaymentStatus.NOT_PAID.value), not_paid_amount_raw), else_=0)
            gst_pending_amount = case((or_(payment_status_filter == None, payment_status_filter == PaymentStatus.GST_PENDING.value), gst_pending_amount_raw), else_=0)
            half_pending_amount = case((or_(payment_status_filter == None, payment_status_filter == PaymentStatus.HALF_PAYMENT_RECEIVED.value), half_pending_amount_raw), else_=0)
            short_pending_amount = case((or_(payment_status_filter == None, payment_status_filter == PaymentStatus.SHORT_PAYMENT_RECEIVED.value), short_pending_amount_raw), else_=0)
            tds_pending_amount = case((or_(payment_status_filter == None, payment_status_filter == PaymentStatus.TDS_PENDING.value), tds_pending_amount_raw), else_=0)


            purchase_type = Orders.logistic_info['purchase_type'].astext

            pivot_query = select(
                Orders.distributor_id,

                func.sum(
                    case((purchase_type == "EXISTING-RENEWAL", customer_final_price), else_=0)
                ).label("existing_renewal"),

                func.sum(
                    case((purchase_type == "NEW-LOGO-RENEWAL", customer_final_price), else_=0)
                ).label("new_logo_renewal"),

                func.sum(
                    case((purchase_type == "NET-NEW-CUSTOMER", customer_final_price), else_=0)
                ).label("net_new_customer"),

                func.sum(
                    case((purchase_type == "EXISTING-ADD-ON", customer_final_price), else_=0)
                ).label("existing_add_on"),
            ).select_from(Orders)


            pivot_query = pivot_query.where(
                *conditions,
                *filters,
                Orders.is_deleted == False
            )

            if date_filter_condition is not None:
                pivot_query = pivot_query.where(date_filter_condition)

            if revenue_filter_condition is not None:
                pivot_query = pivot_query.where(revenue_filter_condition)


            pivot_query = pivot_query \
            .join(Products, Products.id == Orders.product_id, isouter=True) \
            .join(Customers, Customers.id == Orders.customer_id, isouter=True) \
            .join(Distributors, Distributors.id == Orders.distributor_id, isouter=True)
            
            if active_condition is not None:
                pivot_query = pivot_query.where(active_condition)
            pivot_query = pivot_query.group_by(Orders.distributor_id)

            purchase_stats = (await self.session.execute(pivot_query)).mappings().all()


            orders_infos_stmt=(
                select(
                    func.sum(profit_loss_price).label("total_revenue"),
                    func.sum(distri_final_price).label("distributor_value"),
                    func.sum(Orders.quantity).label("total_license"),
                    func.count(Orders.id).label("total_orders"),
                    func.sum(customer_final_price).label("order_value"),
                    func.count().filter(Orders.activated.is_(False)).label("not_activated"),
                    func.sum(invoice_stats_subq.c.pending_invoice).label("pending_invoice"),
                    func.sum(case((or_(payment_status_filter == None, payment_status_filter == PaymentStatus.TDS_PENDING.value), invoice_stats_subq.c.tds_pendings), else_=0)).label("tds_pendings"),
                    func.sum(
                        case((or_(payment_status_filter == None, payment_status_filter == PaymentStatus.TDS_PENDING.value), invoice_stats_subq.c.tds_pendings), else_=0) +
                        case((or_(payment_status_filter == None, payment_status_filter == PaymentStatus.NOT_PAID.value), invoice_stats_subq.c.not_paid_pendings), else_=0) +
                        case((or_(payment_status_filter == None, payment_status_filter == PaymentStatus.GST_PENDING.value), invoice_stats_subq.c.gst_pendings), else_=0) +
                        case((or_(payment_status_filter == None, payment_status_filter == PaymentStatus.HALF_PAYMENT_RECEIVED.value), invoice_stats_subq.c.half_pendings), else_=0) +
                        case((or_(payment_status_filter == None, payment_status_filter == PaymentStatus.SHORT_PAYMENT_RECEIVED.value), invoice_stats_subq.c.short_pendings), else_=0)
                    ).label("tot_pending_dues"),
                    func.sum(vendor_disc_price).label("vendor_value"),
                    func.sum(case((or_(payment_status_filter == None, payment_status_filter == PaymentStatus.NOT_PAID.value), invoice_stats_subq.c.not_paid_pendings), else_=0)).label("not_paid_pendings"),
                    func.sum(case((or_(payment_status_filter == None, payment_status_filter == PaymentStatus.GST_PENDING.value), invoice_stats_subq.c.gst_pendings), else_=0)).label("gst_pendings"),
                    func.sum(case((or_(payment_status_filter == None, payment_status_filter == PaymentStatus.HALF_PAYMENT_RECEIVED.value), invoice_stats_subq.c.half_pendings), else_=0)).label("half_pendings"),
                    func.sum(case((or_(payment_status_filter == None, payment_status_filter == PaymentStatus.SHORT_PAYMENT_RECEIVED.value), invoice_stats_subq.c.short_pendings), else_=0)).label("short_pendings"),
                    func.sum(not_paid_amount).label("not_paid_amounts"),
                    func.sum(tds_pending_amount).label("tds_amounts"),
                    func.sum(gst_pending_amount).label("gst_amounts"),
                    func.sum(half_pending_amount).label("half_amounts"),
                    func.sum(short_pending_amount).label("short_amounts"),
                    func.sum(not_paid_amount + tds_pending_amount + gst_pending_amount + half_pending_amount + short_pending_amount).label("tot_pending_amounts")

                )
                .outerjoin(payment_subq, payment_subq.c.order_id == Orders.id)
                .outerjoin(invoice_stats_subq, invoice_stats_subq.c.order_id == Orders.id)
                .join(Products, Products.id == Orders.product_id, isouter=True)
                .join(Customers, Customers.id == Orders.customer_id, isouter=True)
                .join(Distributors, Distributors.id == Orders.distributor_id, isouter=True)
                .where(*conditions,*filters,Orders.is_deleted==False)
                .where(date_filter_condition if date_filter_condition is not None else true())
                .where(revenue_filter_condition if revenue_filter_condition is not None else true())
            )

            if active_condition is not None:
                orders_infos_stmt = orders_infos_stmt.where(active_condition)

            orders_infos=(await self.session.execute(orders_infos_stmt)).mappings().one_or_none()


        return {
            **orders_infos,
            "purchase_stats": purchase_stats,
            'total_pages':ceil(orders_infos.get('total_orders',0)/limit),
            'next_cursor':queried_orders[-1]['sequence_id'] if (len(queried_orders)>0 and queried_orders[-1]['sequence_id']!=1) else None,
            'orders':queried_orders,

        }
    
    async def search(self,query:str):
        search_term=f"%{query.lower()}%"
        date_expr=func.date(func.timezone("Asia/Kolkata",Orders.created_at))
        queried_orders=(await self.session.execute(
            select(
                *self.orders_cols,
                date_expr.label("order_created_at")  
            )
            .join(self.subquery, self.subquery.c.order_id == Orders.id, isouter=True)
            .join(Products,Products.id==Orders.product_id,isouter=True)
            .join(Customers,Customers.id==Orders.customer_id,isouter=True)
            .join(Distributors,Distributors.id==Orders.distributor_id,isouter=True)
            .join(OrdersPaymentInvoiceInfo, OrdersPaymentInvoiceInfo.order_id == Orders.id,isouter=True)
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
                    Orders.logistic_info['distributor_type'].astext.ilike(search_term),
                    exists().where(
                        and_(
                            OrdersPaymentInvoiceInfo.order_id == Orders.id,
                            OrdersPaymentInvoiceInfo.invoice_number.ilike(search_term)
                        )
                    )
                ),
                Orders.is_deleted==False
            )
            .limit(5)
        )).mappings().all()

        return {'orders':queried_orders}

        
    async def get_by_id(self,order_id:str,include_delete:bool=False):
        date_expr=func.date(func.timezone("Asia/Kolkata",Orders.created_at))
        queried_orders=(await self.session.execute(
            select(
                *self.orders_cols,
                date_expr.label("order_created_at"), 
                Customers.email.label('customer_email')
            )
            .join(self.subquery, self.subquery.c.order_id == Orders.id, isouter=True)
            .join(Products,Products.id==Orders.product_id,isouter=True)
            .join(Customers,Customers.id==Orders.customer_id,isouter=True)
            .join(Distributors,Distributors.id==Orders.distributor_id,isouter=True) 
            .where(or_(Orders.id==order_id,Orders.ui_id==order_id),Orders.is_deleted==include_delete)
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
            .join(self.subquery, self.subquery.c.order_id == Orders.id, isouter=True)
            .join(Products,Products.id==Orders.product_id,isouter=True)
            .join(Customers,Customers.id==Orders.customer_id,isouter=True)
            .join(Distributors,Distributors.id==Orders.distributor_id,isouter=True)
            .where(Orders.customer_id==customer_id,Orders.sequence_id>cursor,Orders.is_deleted==False)

            .limit(limit)
        )).mappings().all()

        orders_infos={}
        ic(cursor)
        if cursor==0:
            payment_subq = (
                select(
                    OrdersPaymentInvoiceInfo.order_id,
                    func.sum(func.coalesce(OrdersPaymentInvoiceInfo.paid_amount, 0)).label("paid_total")
                )
                .group_by(OrdersPaymentInvoiceInfo.order_id)
                .subquery()
            )

            customer_price = (Orders.unit_price * Orders.quantity)

            orders_infos=(await self.session.execute(
                select(
                    func.sum(
                        func.round(customer_price * 1.18) -
                        func.coalesce(payment_subq.c.paid_total, 0)
                    ).filter(and_(OrdersPaymentInvoiceInfo.payment_status != PaymentStatus.PAID.value,OrdersPaymentInvoiceInfo.payment_status != PaymentStatus.FULL_PAYMENT_RECEIVED.value)).label("pending_amounts"),
                    func.sum(profit_loss_price).label("total_revenue"),
                    func.count(Orders.id).label("total_orders"),
                    func.sum(customer_final_price).label("order_value"),
                    func.count(OrdersPaymentInvoiceInfo.id).filter(OrdersPaymentInvoiceInfo.invoice_status == InvoiceStatus.INCOMPLETED.value).label("pending_invoice"),
                    func.count().filter(and_(OrdersPaymentInvoiceInfo.payment_status != PaymentStatus.PAID.value,OrdersPaymentInvoiceInfo.payment_status != PaymentStatus.FULL_PAYMENT_RECEIVED.value)).label("pending_dues")
                )
                .outerjoin(
                    payment_subq, payment_subq.c.order_id == Orders.id
                )
                .join(OrdersPaymentInvoiceInfo,OrdersPaymentInvoiceInfo.order_id==Orders.id,isouter=True)
                .join(Products, Products.id == Orders.product_id, isouter=True)
                .join(Customers, Customers.id == Orders.customer_id, isouter=True)
                .join(Distributors, Distributors.id == Orders.distributor_id, isouter=True)
                .join(Users, Users.id == Orders.deleted_by, isouter=True)
                .where(Orders.customer_id==customer_id,Orders.is_deleted==False)
            )).mappings().one_or_none()

        ic(orders_infos)
        ic(queried_orders)

        return {
            **orders_infos,
            'orders':queried_orders,
            'total_pages':ceil(orders_infos.get('total_orders',0)/limit),
            'next_cursor':queried_orders[-1]['sequence_id'] if len(queried_orders)>0 else None
        }
    

    async def get_last_order(self,customer_id:str,product_id:str):
        date_expr=cast(
            Orders.delivery_info['delivery_date'].astext,
            Date
        )

        expiry_expr = cast(
            date_expr + text(f"INTERVAL '{DEFAULT_ADDON_YEAR + 1} days'"),
            Date
        )

        last_ord_stmt=(
            select(
                Orders.id,
                Orders.unit_price,
                Orders.logistic_info,
                Orders.delivery_info,
                date_expr.label("last_date"),
                expiry_expr.label("expiry_date")
            )
            .where(
                Orders.customer_id==customer_id,
                Orders.product_id==product_id,
                Orders.is_deleted==False,
                Orders.logistic_info['purchase_type'].astext!=PurchaseTypes.EXISTING_ADD_ON.value
            )
            .order_by(desc(date_expr))
        )
         
        last_ord=(await self.session.execute(last_ord_stmt)).mappings().all()
        return {'last_order':last_ord}
        return {'last_order':{**last_ord,'expiry_date':last_ord['last_date']+timedelta(days=DEFAULT_ADDON_YEAR+1)}if last_ord else last_ord}
    

    async def test(self,cursor:int=1,limit:int=10,query:str='',include_deleted:Optional[bool]=False):
        payment_subq = (
                select(
                    OrdersPaymentInvoiceInfo.order_id,

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

                    func.coalesce(
                        OrdersPaymentInvoiceInfo.paid_amount, 0
                    ).label("total_paid_amount")

                )
                .group_by(OrdersPaymentInvoiceInfo.order_id)
                .subquery()
            )
        result=(await self.session.execute(
            select(
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
                Orders.logistic_info,Products.name.label('product_name'),
                Products.product_type,
                Products.description,
                Products.price.label('product_price'),
                Customers.name.label('customer_name'),
                Customers.mobile_number,
                Distributors.name.label('distributor_name'),
                distri_discount.label('distributor_discount'),
                Orders.unit_price,
                Orders.vendor_commision,
                payment_subq.c.status_info,
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
                customer_amount_with_gst.label('customer_amount_with_gst'),
                func.date(expiry_date).label("last_order_expiry_date")
            )
            .limit(limit=limit)
            .join(payment_subq, payment_subq.c.order_id == Orders.id, isouter=True)
            .join(Products,Products.id==Orders.product_id,isouter=True)
            .join(Customers,Customers.id==Orders.customer_id,isouter=True)
            .join(Distributors,Distributors.id==Orders.distributor_id,isouter=True)
        )
        
        ).mappings().all()
        # payment_subq = (
        #         select(
        #             OrdersPaymentInvoiceInfo.order_id,
        #             func.sum(func.coalesce(OrdersPaymentInvoiceInfo.paid_amount, 0)).label("paid_total")
        #         )
        #         .group_by(OrdersPaymentInvoiceInfo.order_id)
        #         .subquery()
        #     )
        
        # customer_price = (Orders.unit_price * Orders.quantity)
        # orders_infos=(await self.session.execute(
        #         select(
        #             func.sum(
        #                 func.round(customer_price * 1.18) -
        #                 func.coalesce(payment_subq.c.paid_total, 0)
        #             ).filter(and_(OrdersPaymentInvoiceInfo.payment_status != PaymentStatus.PAID.value,OrdersPaymentInvoiceInfo.payment_status != PaymentStatus.FULL_PAYMENT_RECEIVED.value)).label("pending_amounts"),
        #             func.sum(func.distinct(profit_loss_price)).label("total_revenue"),
        #             func.count(func.distinct(Orders.id)).label("total_orders"),
        #             func.sum(func.distinct(customer_final_price)).label("order_value"),
        #             func.count(func.distinct(OrdersPaymentInvoiceInfo.id)).filter(OrdersPaymentInvoiceInfo.invoice_status == InvoiceStatus.INCOMPLETED.value).label("pending_invoice"),
        #             func.count().filter(and_(OrdersPaymentInvoiceInfo.payment_status != PaymentStatus.PAID.value,OrdersPaymentInvoiceInfo.payment_status != PaymentStatus.FULL_PAYMENT_RECEIVED.value)).label("pending_dues")
        #         )
        #         .outerjoin(
        #             payment_subq, payment_subq.c.order_id == Orders.id
        #         )
        #         .join(OrdersPaymentInvoiceInfo,OrdersPaymentInvoiceInfo.order_id==Orders.id,isouter=True)
        #         .join(Products, Products.id == Orders.product_id, isouter=True)
        #         .join(Customers, Customers.id == Orders.customer_id, isouter=True)
        #         .join(Distributors, Distributors.id == Orders.distributor_id, isouter=True)
        #         .join(Users, Users.id == Orders.deleted_by, isouter=True)
        #     )).mappings().one_or_none()
        return result
    

    async def dummy_tes(self):
        ic("hello")
        purchase_type = Orders.logistic_info['purchase_type'].astext

        res = select(
            Orders.distributor_id,


            func.sum(
                case((purchase_type == "EXISTING-RENEWAL", customer_final_price), else_=0)
            ).label("existing_renewal"),

            func.sum(
                case((purchase_type == "NEW-LOGO-RENEWAL", customer_final_price), else_=0)
            ).label("new_logo_renewal"),

            func.sum(
                case((purchase_type == "NET-NEW-CUSTOMER", customer_final_price), else_=0)
            ).label("net_new_customer"),

            func.sum(
                case((purchase_type == "EXISTING-ADD-ON", customer_final_price), else_=0)
            ).label("existing_add_on"),
        ).group_by(Orders.distributor_id)
        result=(await self.session.execute(res)).mappings().all()
        ic(result)
        return result
    

    async def get_cust_distri(self,customer_id: str):
        stmt=(
            select(
                Distributors.name,
                Distributors.id
            )
            .where(
                Orders.customer_id==customer_id,
                Distributors.is_deleted==False,
                Orders.is_deleted==False
            )
            .select_from(Orders)
            .join(Distributors,Distributors.id==Orders.distributor_id,isouter=True)
            .group_by(
                Distributors.id
            )
        )
    

        results=(await self.session.execute(stmt)).mappings().all()

        ic(results)

        return results
    

    async def get_cust_prod(self,customer_id:str,distributor_id:str):
        stmt=(
            select(
                Products.id,
                Products.name
            )
            .where(
                Orders.customer_id==customer_id,
                Orders.distributor_id==distributor_id,
                Products.is_deleted==False,
                Orders.is_deleted==False
            )
            .select_from(Orders)
            .join(
                Products,Products.id==Orders.product_id,isouter=True)
        )

        results=(await self.session.execute(stmt)).mappings().all()

        ic(results)

        return results
    
    async def get_cust_order(self,customer_id:str,distributor_id:str,product_id:str):
        stmt=(
            select(
                *self.orders_cols
            )
            .where(
                Orders.product_id==product_id,
                Orders.customer_id==customer_id,
                Orders.distributor_id==distributor_id,
                Orders.is_deleted==False
            )
            .select_from(Orders)
            .join(self.subquery, self.subquery.c.order_id == Orders.id, isouter=True)
            .join(Products,Products.id==Orders.product_id,isouter=True)
            .join(Customers,Customers.id==Orders.customer_id,isouter=True)
            .join(Distributors,Distributors.id==Orders.distributor_id,isouter=True)
        )

        results=(await self.session.execute(stmt)).mappings().all()
        ic(results)
        
        return results
        

    async def get_order_tracking_report(self,from_date,to_date,owner_name=None,date_by=None):
        """
        Order Tracking Report grouped by customer owner.
        
        Columns:
        1. activation_done_invoice_pending: activated=True, all invoices INCOMPLETED
        2. payment_pending: invoice COMPLETED but payment not fully settled
        3. po_received_activation_pending: activated=False, all invoices INCOMPLETED
        """
        from schemas.request_schemas.order import OrderTrackingReportSchema
        from core.data_formats.enums.order_enums import OrderFilterDateByEnum

        # --- Subquery: per-order invoice/payment aggregation ---
        invoice_agg_subq = (
            select(
                OrdersPaymentInvoiceInfo.order_id,

                # Whether any COMPLETED invoice exists
                func.bool_or(
                    OrdersPaymentInvoiceInfo.invoice_status == InvoiceStatus.COMPLETED.value
                ).label("has_completed_invoice"),

                # Whether ALL invoices are INCOMPLETED (no completed invoice)
                func.bool_and(
                    OrdersPaymentInvoiceInfo.invoice_status == InvoiceStatus.INCOMPLETED.value
                ).label("all_invoices_incompleted"),

                # Whether any payment is pending (not PAID / not FULL_PAYMENT_RECEIVED)
                func.bool_or(
                    and_(
                        OrdersPaymentInvoiceInfo.invoice_status == InvoiceStatus.COMPLETED.value,
                        OrdersPaymentInvoiceInfo.payment_status.notin_([
                            PaymentStatus.PAID.value,
                            PaymentStatus.FULL_PAYMENT_RECEIVED.value
                        ])
                    )
                ).label("has_pending_payment"),

                # Total paid amount
                func.coalesce(
                    func.sum(OrdersPaymentInvoiceInfo.paid_amount), 0
                ).label("total_paid"),
            )
            .group_by(OrdersPaymentInvoiceInfo.order_id)
            .subquery()
        )

        # --- Owner label: coalesce null/empty to 'Others' ---
        owner_label = func.coalesce(
            func.nullif(func.trim(Customers.owner), ''),
            'Others'
        ).label("owner_name")

        # --- Date field to filter on ---
        date_by_val = None
        if date_by:
            date_by_val = date_by.value if hasattr(date_by, 'value') else date_by

        if date_by_val == OrderFilterDateByEnum.REQUESTED_DATE.value:
            date_field = cast(Orders.delivery_info["requested_date"].astext, Date)
        elif date_by_val == OrderFilterDateByEnum.CREATED_DATE.value:
            date_field = cast(Orders.created_at, Date)
        else:
            # Default: ACTIVATION_DATE (delivery_date)
            date_field = cast(Orders.delivery_info["delivery_date"].astext, Date)

        # --- Conditions ---
        conditions = [
            Orders.is_deleted == False,
            date_field >= from_date,
            date_field <= to_date,
        ]

        if owner_name:
            conditions.append(Customers.owner == owner_name)

        # --- CASE expressions for the three columns ---

        # 1) Activation done, invoice need to raise:
        #    activated=True AND all invoices are INCOMPLETED
        activation_done_invoice_pending = func.coalesce(func.sum(
            case(
                (
                    and_(
                        Orders.activated == True,
                        func.coalesce(invoice_agg_subq.c.all_invoices_incompleted, True) == True,
                    ),
                    customer_final_price
                ),
                else_=0
            )
        ), 0)

        # 2) Payment pending:
        #    Has completed invoice but payment is pending
        #    Value = customer_price_with_gst - total_paid
        payment_pending_val = func.coalesce(func.sum(
            case(
                (
                    and_(
                        func.coalesce(invoice_agg_subq.c.has_completed_invoice, False) == True,
                        func.coalesce(invoice_agg_subq.c.has_pending_payment, False) == True,
                    ),
                    func.greatest(
                        func.round(cast(customer_final_price_inc_gst, Numeric)) - func.coalesce(invoice_agg_subq.c.total_paid, 0),
                        0
                    )
                ),
                else_=0
            )
        ), 0)

        # 3) PO received, activation need to done:
        #    activated=False AND all invoices INCOMPLETED (or no invoice)
        po_received_activation_pending = func.coalesce(func.sum(
            case(
                (
                    and_(
                        Orders.activated == False,
                        func.coalesce(invoice_agg_subq.c.all_invoices_incompleted, True) == True,
                    ),
                    customer_final_price
                ),
                else_=0
            )
        ), 0)

        # --- Main aggregation query ---
        report_stmt = (
            select(
                owner_label,
                func.round(cast(activation_done_invoice_pending, Numeric)).label("activation_done_invoice_pending"),
                func.round(cast(payment_pending_val, Numeric), 2).label("payment_pending"),
                func.round(cast(po_received_activation_pending, Numeric)).label("po_received_activation_pending"),
                func.round(
                    cast(activation_done_invoice_pending + payment_pending_val + po_received_activation_pending, Numeric), 2
                ).label("grand_total"),
            )
            .select_from(Orders)
            .outerjoin(invoice_agg_subq, invoice_agg_subq.c.order_id == Orders.id)
            .join(Products, Products.id == Orders.product_id, isouter=True)
            .join(Customers, Customers.id == Orders.customer_id, isouter=True)
            .join(Distributors, Distributors.id == Orders.distributor_id, isouter=True)
            .where(*conditions)
            .group_by(owner_label)
            .order_by(owner_label)
        )

        owner_rows = (await self.session.execute(report_stmt)).mappings().all()

        # --- Grand total row ---
        grand_total_stmt = (
            select(
                func.round(cast(func.coalesce(func.sum(
                    case(
                        (
                            and_(
                                Orders.activated == True,
                                func.coalesce(invoice_agg_subq.c.all_invoices_incompleted, True) == True,
                            ),
                            customer_final_price
                        ),
                        else_=0
                    )
                ), 0), Numeric)).label("activation_done_invoice_pending"),
                func.round(cast(func.coalesce(func.sum(
                    case(
                        (
                            and_(
                                func.coalesce(invoice_agg_subq.c.has_completed_invoice, False) == True,
                                func.coalesce(invoice_agg_subq.c.has_pending_payment, False) == True,
                            ),
                            func.greatest(
                                func.round(cast(customer_final_price_inc_gst, Numeric)) - func.coalesce(invoice_agg_subq.c.total_paid, 0),
                                0
                            )
                        ),
                        else_=0
                    )
                ), 0), Numeric), 2).label("payment_pending"),
                func.round(cast(func.coalesce(func.sum(
                    case(
                        (
                            and_(
                                Orders.activated == False,
                                func.coalesce(invoice_agg_subq.c.all_invoices_incompleted, True) == True,
                            ),
                            customer_final_price
                        ),
                        else_=0
                    )
                ), 0), Numeric)).label("po_received_activation_pending"),
            )
            .select_from(Orders)
            .outerjoin(invoice_agg_subq, invoice_agg_subq.c.order_id == Orders.id)
            .join(Products, Products.id == Orders.product_id, isouter=True)
            .join(Customers, Customers.id == Orders.customer_id, isouter=True)
            .join(Distributors, Distributors.id == Orders.distributor_id, isouter=True)
            .where(*conditions)
        )

        grand_total_row = (await self.session.execute(grand_total_stmt)).mappings().one_or_none()

        grand_total = {
            "activation_done_invoice_pending": float(grand_total_row["activation_done_invoice_pending"] or 0),
            "payment_pending": float(grand_total_row["payment_pending"] or 0),
            "po_received_activation_pending": float(grand_total_row["po_received_activation_pending"] or 0),
        }
        grand_total["grand_total"] = round(
            grand_total["activation_done_invoice_pending"] +
            grand_total["payment_pending"] +
            grand_total["po_received_activation_pending"], 2
        )

        owners_data = []
        for row in owner_rows:
            owners_data.append({
                "owner_name": row["owner_name"],
                "activation_done_invoice_pending": float(row["activation_done_invoice_pending"] or 0),
                "payment_pending": float(row["payment_pending"] or 0),
                "po_received_activation_pending": float(row["po_received_activation_pending"] or 0),
                "grand_total": float(row["grand_total"] or 0),
            })

        return {
            "owners": owners_data,
            "grand_total": grand_total
        }


    async def get_payment_pending_report(self,from_date,to_date,owner_name=None,min_days_pending=None,date_by=None):
        """
        Payment Pending Report grouped by customer owner with aging buckets.
        
        Buckets:
        1. 1-8 days: invoice_count + pending_value
        2. 8-16 days: invoice_count + pending_value
        3. 16-30 days: invoice_count + pending_value
        4. >30 days: invoice_count + pending_value
        + Grand Total per owner
        """
        from core.data_formats.enums.order_enums import OrderFilterDateByEnum

        # --- Owner label ---
        owner_label = func.coalesce(
            func.nullif(func.trim(Customers.owner), ''),
            'Others'
        ).label("owner_name")

        # --- Date field to filter on ---
        date_by_val = None
        if date_by:
            date_by_val = date_by.value if hasattr(date_by, 'value') else date_by

        if date_by_val == OrderFilterDateByEnum.REQUESTED_DATE.value:
            date_field = cast(Orders.delivery_info["requested_date"].astext, Date)
        elif date_by_val == OrderFilterDateByEnum.CREATED_DATE.value:
            date_field = cast(Orders.created_at, Date)
        else:
            date_field = cast(Orders.delivery_info["delivery_date"].astext, Date)

        # --- Invoice date as Date and days_pending ---
        invoice_date_field = cast(OrdersPaymentInvoiceInfo.invoice_date, Date)
        days_pending = func.greatest(
            func.current_date() - invoice_date_field,
            0
        )

        # --- Get total invoices and pending invoices per order ---
        invoice_stats_subq = (
            select(
                OrdersPaymentInvoiceInfo.order_id,
                func.count().label("total_invoices"),
                func.count().filter(
                    and_(
                        OrdersPaymentInvoiceInfo.invoice_status == InvoiceStatus.COMPLETED.value,
                        OrdersPaymentInvoiceInfo.payment_status.notin_([
                            PaymentStatus.PAID.value,
                            PaymentStatus.FULL_PAYMENT_RECEIVED.value
                        ])
                    )
                ).label("matching_invoices")
            )
            .group_by(OrdersPaymentInvoiceInfo.order_id)
            .subquery()
        )

        # --- Invoice Value = full order amount (distributed across matching pending invoices to avoid duplication)
        invoice_total_value = func.round(
            cast(customer_final_price_inc_gst, Numeric) / func.nullif(invoice_stats_subq.c.matching_invoices, 0)
        )

        # --- Pending Value = expected invoice amount minus paid amount ---
        split_expected_amount = func.round(
            cast(customer_final_price_inc_gst, Numeric) / func.nullif(invoice_stats_subq.c.total_invoices, 0)
        )
        invoice_pending_value = func.greatest(
            split_expected_amount - func.coalesce(OrdersPaymentInvoiceInfo.paid_amount, 0),
            0
        )

        # --- Conditions: only COMPLETED invoices with pending payment ---
        conditions = [
            Orders.is_deleted == False,
            date_field >= from_date,
            date_field <= to_date,
            OrdersPaymentInvoiceInfo.invoice_status == InvoiceStatus.COMPLETED.value,
            OrdersPaymentInvoiceInfo.payment_status.notin_([
                PaymentStatus.PAID.value,
                PaymentStatus.FULL_PAYMENT_RECEIVED.value
            ]),
        ]

        if owner_name and owner_name.upper() != 'ALL':
            conditions.append(Customers.owner == owner_name)

        if min_days_pending is not None and min_days_pending > 0:
            conditions.append(days_pending >= min_days_pending)

        # --- Owner-level totals subquery ---
        owner_totals_subq = (
            select(
                owner_label.label("owner_name_key"),
                func.count().label("owner_invoice_count"),
                func.round(cast(func.coalesce(func.sum(invoice_total_value), 0), Numeric), 2).label("owner_invoice_amount"),
                func.round(cast(func.coalesce(func.sum(invoice_pending_value), 0), Numeric), 2).label("owner_pending_amount")
            )
            .select_from(Orders)
            .join(OrdersPaymentInvoiceInfo, OrdersPaymentInvoiceInfo.order_id == Orders.id)
            .join(Products, Products.id == Orders.product_id, isouter=True)
            .join(Customers, Customers.id == Orders.customer_id, isouter=True)
            .join(Distributors, Distributors.id == Orders.distributor_id, isouter=True)
            .join(invoice_stats_subq, invoice_stats_subq.c.order_id == Orders.id)
            .where(*conditions)
            .group_by(owner_label)
            .subquery()
        )

        # --- Main aggregation query ---
        report_stmt = (
            select(
                owner_label,
                Customers.name.label("customer_name"),
                Orders.ui_id.label("order_id"),
                func.count().label("invoice_count"),
                func.round(cast(func.coalesce(func.sum(invoice_total_value), 0), Numeric), 2).label("invoice_amount"),
                func.round(cast(func.coalesce(func.sum(invoice_pending_value), 0), Numeric), 2).label("pending_amount")
            )
            .select_from(Orders)
            .join(OrdersPaymentInvoiceInfo, OrdersPaymentInvoiceInfo.order_id == Orders.id)
            .join(Products, Products.id == Orders.product_id, isouter=True)
            .join(Customers, Customers.id == Orders.customer_id, isouter=True)
            .join(Distributors, Distributors.id == Orders.distributor_id, isouter=True)
            .join(invoice_stats_subq, invoice_stats_subq.c.order_id == Orders.id)
            .where(*conditions)
            .group_by(owner_label, Customers.name, Orders.ui_id)
            .order_by(owner_label, Customers.name, Orders.ui_id)
        )

        owner_rows = (await self.session.execute(report_stmt)).mappings().all()

        # --- Owner-level summary list ---
        summary_stmt = select(
            owner_totals_subq.c.owner_name_key.label("owner_name"),
            owner_totals_subq.c.owner_invoice_count,
            owner_totals_subq.c.owner_invoice_amount,
            owner_totals_subq.c.owner_pending_amount
        ).order_by("owner_name")
        
        summary_rows = (await self.session.execute(summary_stmt)).mappings().all()
        
        owner_summaries = []
        for s in summary_rows:
            owner_summaries.append({
                "owner_name": s["owner_name"],
                "total_invoice_count": int(s["owner_invoice_count"] or 0),
                "total_invoice_amount": float(s["owner_invoice_amount"] or 0),
                "total_pending_amount": float(s["owner_pending_amount"] or 0),
            })

        # --- Grand total row ---
        grand_total_stmt = (
            select(
                func.count().label("invoice_count"),
                func.round(cast(func.coalesce(func.sum(invoice_total_value), 0), Numeric), 2).label("invoice_amount"),
                func.round(cast(func.coalesce(func.sum(invoice_pending_value), 0), Numeric), 2).label("pending_amount")
            )
            .select_from(Orders)
            .join(OrdersPaymentInvoiceInfo, OrdersPaymentInvoiceInfo.order_id == Orders.id)
            .join(Products, Products.id == Orders.product_id, isouter=True)
            .join(Customers, Customers.id == Orders.customer_id, isouter=True)
            .join(Distributors, Distributors.id == Orders.distributor_id, isouter=True)
            .join(invoice_stats_subq, invoice_stats_subq.c.order_id == Orders.id)
            .where(*conditions)
        )

        gt_row = (await self.session.execute(grand_total_stmt)).mappings().one_or_none()

        # --- Format results ---
        owners_data = []
        for row in owner_rows:
            owners_data.append({
                "owner_name": row["owner_name"],
                "customer_name": row["customer_name"],
                "order_id": row["order_id"],
                "invoice_count": int(row["invoice_count"] or 0),
                "invoice_amount": float(row["invoice_amount"] or 0),
                "pending_amount": float(row["pending_amount"] or 0),
            })

        grand_total = {
            "invoice_count": int(gt_row["invoice_count"] or 0) if gt_row else 0,
            "invoice_amount": float(gt_row["invoice_amount"] or 0) if gt_row else 0,
            "pending_amount": float(gt_row["pending_amount"] or 0) if gt_row else 0,
        }

        return {
            "owner_summaries": owner_summaries,
            "grand_total": grand_total
        }

    async def get_distributor_projection_report(self, distributor_id, from_date, to_date, starting_month=None, date_by=OrderFilterDateByEnum.CREATED_DATE.value):
        """
        Distributor Projection Report grouped by order creation month with 12-month projections.
        """
        # Determine which date field to use based on date_by
        if date_by == OrderFilterDateByEnum.ACTIVATION_DATE.value:
            date_field = cast(Orders.delivery_info["delivery_date"].astext, Date)
        elif date_by == OrderFilterDateByEnum.REQUESTED_DATE.value:
            date_field = cast(Orders.delivery_info["requested_date"].astext, Date)
        else:
            # Default to created_at with IST timezone for consistency with dashboard
            date_field = func.date(func.timezone("Asia/Kolkata", Orders.created_at))

        # Re-derive month expressions from the selected date_field
        # If date_field is already a Date type (from cast), we can just use to_char on it
        order_month_expr = func.to_char(date_field, "Mon-YY")
        order_month_sort = func.date_trunc("month", date_field)

        conditions = [
            Orders.is_deleted == False,
            Orders.distributor_id == distributor_id,
            date_field >= from_date,
            date_field <= to_date,
        ]

        report_stmt = (
            select(
                order_month_expr.label("order_month"),
                order_month_sort.label("order_month_sort"),
                func.sum(distri_final_price).label("total_value")
            )
            .select_from(Orders)
            .join(Products, Products.id == Orders.product_id, isouter=True)
            .join(Distributors, Distributors.id == Orders.distributor_id, isouter=True)
            .where(*conditions)
            .group_by(order_month_expr, order_month_sort)
            .order_by(desc(order_month_sort))
        )

        rows = (await self.session.execute(report_stmt)).mappings().all()

        result_rows = []
        all_columns = set()

        if starting_month:
            try:
                # Expecting YYYY-MM
                ref_date_obj = datetime.strptime(starting_month, "%Y-%m").date()
            except Exception:
                ref_date_obj = date.today().replace(day=1)
        else:
            ref_date_obj = date.today().replace(day=1)

        current_month_str = ref_date_obj.strftime("%b-%y").lower()

        for row in rows:
            order_month_str = row["order_month"]
            total_value = float(row["total_value"] or 0)
            split_value = round(total_value / 12, 2) if total_value else 0
            
            # Base month object (the actual month of the order)
            base_date = row["order_month_sort"]
            if hasattr(base_date, 'replace'):
                base_date = base_date.replace(tzinfo=None)
            
            # Ensure base_date is a date or datetime
            if isinstance(base_date, str):
                base_date = datetime.datetime.strptime(base_date[:10], "%Y-%m-%d")

            projections = []
            
            for i in range(1, 13):
                # Calculate future month and year
                proj_month = base_date.month + i
                proj_year = base_date.year + ((proj_month - 1) // 12)
                proj_month = ((proj_month - 1) % 12) + 1
                
                # Format exactly as "%b-%y" (e.g., "Jun-25")
                proj_date_obj = date(proj_year, proj_month, 1)
                proj_month_str = proj_date_obj.strftime("%b-%y")
                
                # Ensure all 12 months of this year are in the columns list to satisfy "where is jan feb"
                for m in range(1, 13):
                    m_date = date(proj_year, m, 1)
                    all_columns.add((proj_year, m, m_date.strftime("%b-%y")))
                
                # Logic: All months on or before the reference month are "happy" (received/current)
                # All months after the reference month are "bad" (to be collected)
                is_happy = proj_date_obj <= ref_date_obj
                
                projections.append({
                    "month": proj_month_str,
                    "amount": split_value,
                    "type": "happy" if is_happy else "bad"
                })
                
            total_happy = 0
            total_bad = 0
            for proj in projections:
                if proj["type"] == "happy":
                    total_happy += proj["amount"]
                else:
                    total_bad += proj["amount"]

            result_rows.append({
                "month": order_month_str,
                "total_value": total_value,
                "split_value": split_value,
                "total_happy": round(total_happy, 2),
                "total_bad": round(total_bad, 2),
                "projection": projections
            })

        # Sort columns chronologically by year then month
        sorted_cols = [x[2] for x in sorted(list(all_columns), key=lambda x: (x[0], x[1]))]

        return {
            "rows": result_rows,
            "columns": sorted_cols
        }






class OrderTrackingReportRepo(OrdersRepo):
    async def get(self, **kwargs):
        # We only return data for the first page since it's a summary
        if kwargs.get('cursor') != 1:
            return {"owners": [], "next_cursor": None}
            
        from_date = kwargs.get('from_date')
        to_date = kwargs.get('to_date')
        if isinstance(from_date, str):
            from_date = datetime.strptime(from_date[:10], "%Y-%m-%d").date()
        if isinstance(to_date, str):
            to_date = datetime.strptime(to_date[:10], "%Y-%m-%d").date()

        report = await self.get_order_tracking_report(
            from_date=from_date,
            to_date=to_date,
            owner_name=kwargs.get('owner_name'),
            date_by=kwargs.get('date_by')
        )
        
        owners = report['owners']
        gt = report['grand_total']
        gt['owner_name'] = 'Grand Total'
        gt['customer_name'] = ''
        gt['order_id'] = ''
        owners.append(gt)
        
        return {
            "owners": owners,
            "next_cursor": None
        }

class PaymentPendingReportRepo(OrdersRepo):
    async def get(self, **kwargs):
        if kwargs.get('cursor') != 1:
            return {"owners": [], "next_cursor": None}
            
        from_date = kwargs.get('from_date')
        to_date = kwargs.get('to_date')
        if isinstance(from_date, str):
            from_date = datetime.strptime(from_date[:10], "%Y-%m-%d").date()
        if isinstance(to_date, str):
            to_date = datetime.strptime(to_date[:10], "%Y-%m-%d").date()

        report = await self.get_payment_pending_report(
            from_date=from_date,
            to_date=to_date,
            owner_name=kwargs.get('owner_name'),
            min_days_pending=kwargs.get('min_days_pending'),
            date_by=kwargs.get('date_by')
        )
        
        owners = report['owners']
        gt = report['grand_total']
        gt['owner_name'] = 'Total'
        gt['customer_name'] = ''
        gt['order_id'] = ''
        owners.append(gt)
        
        return {
            "owners": owners,
            "next_cursor": None
        }

class DistributorProjectionReportRepo(OrdersRepo):
    async def get(self, **kwargs):
        cursor = kwargs.get('cursor', 1)
        if cursor is not None and int(cursor) != 1:
            return {"rows": [], "columns": [], "next_cursor": None}
            
        from_date = kwargs.get('from_date')
        to_date = kwargs.get('to_date')
        
        # Convert strings back to dates if they came from JSON serialization in background jobs
        if isinstance(from_date, str):
            from_date = datetime.strptime(from_date[:10], "%Y-%m-%d").date()
        if isinstance(to_date, str):
            to_date = datetime.strptime(to_date[:10], "%Y-%m-%d").date()

        report = await self.get_distributor_projection_report(
            distributor_id=kwargs.get('distributor_id'),
            from_date=from_date,
            to_date=to_date,
            date_by=kwargs.get('date_by')
        )
        
        return {
            "rows": report["rows"],
            "columns": report["columns"],
            "next_cursor": None
        }



