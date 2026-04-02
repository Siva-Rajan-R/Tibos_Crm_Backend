from typing import cast,List
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
            'owner_name':Customers.owner
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
            if value is None:
                continue

            if key == "payment_status":
                filters.append(
                    exists().where(
                        and_(
                            OrdersPaymentInvoiceInfo.order_id == Orders.id,
                            OrdersPaymentInvoiceInfo.payment_status == value
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

                    func.count().filter(
                        OrdersPaymentInvoiceInfo.invoice_status == InvoiceStatus.INCOMPLETED.value
                    ).label("pending_invoice"),

                    func.count().filter(
                        OrdersPaymentInvoiceInfo.payment_status == PaymentStatus.TDS_PENDING.value
                    ).label("tds_pendings"),

                    func.count().filter(
                        OrdersPaymentInvoiceInfo.payment_status == PaymentStatus.NOT_PAID.value
                    ).label("not_paid_pendings"),

                    func.count().filter(
                        OrdersPaymentInvoiceInfo.payment_status == PaymentStatus.GST_PENDING.value
                    ).label("gst_pendings"),

                    func.count().filter(
                        OrdersPaymentInvoiceInfo.payment_status == PaymentStatus.HALF_PAYMENT_RECEIVED.value
                    ).label("half_pendings"),

                    func.count().filter(
                        OrdersPaymentInvoiceInfo.payment_status == PaymentStatus.SHORT_PAYMENT_RECEIVED.value
                    ).label("short_pendings"),
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

            pending_amount_expr = func.greatest(
                customer_amount_with_gst -
                func.coalesce(payment_subq.c.paid_total, 0),
                0
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


            not_paid_amount = case(
                (func.coalesce(invoice_stats_subq.c.not_paid_pendings, 0) > 0, pending_amount_expr),
                else_=0
            )

            tds_pending_amount = case(
                (func.coalesce(invoice_stats_subq.c.tds_pendings, 0) > 0, pending_amount_expr),
                else_=0
            )

            gst_pending_amount = case(
                (func.coalesce(invoice_stats_subq.c.gst_pendings, 0) > 0, pending_amount_expr),
                else_=0
            )

            half_pending_amount = case(
                (func.coalesce(invoice_stats_subq.c.half_pendings, 0) > 0, pending_amount_expr),
                else_=0
            )

            short_pending_amount = case(
                (func.coalesce(invoice_stats_subq.c.short_pendings, 0) > 0, pending_amount_expr),
                else_=0
            )



            orders_infos=(await self.session.execute(
                select(
                    func.sum(profit_loss_price).label("total_revenue"),
                    func.sum(distri_final_price).label("distributor_value"),
                    func.sum(Orders.quantity).label("total_license"),
                    func.count(Orders.id).label("total_orders"),
                    func.sum(customer_final_price).label("order_value"),
                    func.count().filter(Orders.activated.is_(False)).label("not_activated"),
                    func.sum(invoice_stats_subq.c.pending_invoice).label("pending_invoice"),
                    func.sum(invoice_stats_subq.c.tds_pendings).label("tds_pendings"),
                    func.count().filter(
                        (
                            func.coalesce(invoice_stats_subq.c.not_paid_pendings, 0) +
                            func.coalesce(invoice_stats_subq.c.tds_pendings, 0) +
                            func.coalesce(invoice_stats_subq.c.gst_pendings, 0) +
                            func.coalesce(invoice_stats_subq.c.half_pendings, 0) +
                            func.coalesce(invoice_stats_subq.c.short_pendings, 0)
                        ) > 0
                    ).label("tot_pending_dues"),
                    func.sum(vendor_disc_price).label("vendor_value"),
                    func.sum(invoice_stats_subq.c.not_paid_pendings).label("not_paid_pendings"),
                    func.sum(invoice_stats_subq.c.gst_pendings).label("gst_pendings"),
                    func.sum(invoice_stats_subq.c.half_pendings).label("half_pendings"),
                    func.sum(invoice_stats_subq.c.short_pendings).label("short_pendings"),
                    func.sum(not_paid_amount).label("not_paid_amounts"),
                    func.sum(tds_pending_amount).label("tds_amounts"),
                    func.sum(gst_pending_amount).label("gst_amounts"),
                    func.sum(half_pending_amount).label("half_amounts"),
                    func.sum(short_pending_amount).label("short_amounts"),
                    func.sum(pending_amount_expr).label("tot_pending_amounts")

                )
                .outerjoin(payment_subq, payment_subq.c.order_id == Orders.id)
                .outerjoin(invoice_stats_subq, invoice_stats_subq.c.order_id == Orders.id)
                .join(Products, Products.id == Orders.product_id, isouter=True)
                .join(Customers, Customers.id == Orders.customer_id, isouter=True)
                .join(Distributors, Distributors.id == Orders.distributor_id, isouter=True)
                .where(*conditions,*filters,Orders.is_deleted==False)
                .where(date_filter_condition if date_filter_condition is not None else true())
                .where(revenue_filter_condition if revenue_filter_condition is not None else true())
            )).mappings().one_or_none()


        return {
            **orders_infos,
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
                    Orders.logistic_info['distributor_type'].astext.ilike(search_term)
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
    




