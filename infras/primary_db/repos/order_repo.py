from typing import cast,List
import io
import pandas as pd
from datetime import datetime, timedelta, date
from . import HTTPException,BaseRepoModel
from ..models.order import Orders,OrdersPaymentInvoiceInfo,OrderRenewals,OrderAddOns,CartOrders,CartOrdersPaymentInvoiceInfo
from core.utils.uuid_generator import generate_uuid
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
            OrderAddOns.base_quantity.label("addon_base_quantity"),
            OrderAddOns.addon_quantity.label("addon_quantity"),
            OrderAddOns.base_price.label("addon_base_price"),
            OrderAddOns.addon_price.label("addon_price"),
            OrderAddOns.remaining_days.label("addon_remaining_days"),
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
        new_order = Orders(**data.model_dump(mode='json',exclude=['lui_id','status_info']))
        self.session.add(new_order)
        invoicetoadd=data.model_dump(mode='json')
        invoicetoadd_bulk=[]
        for status in invoicetoadd['status_info']:
            if status.get("payment_status") in ("FULL PAYMENT RECEIVED", "PAID"):
                status["paid_amount"] = status.get("paid_amount") if status.get("paid_amount") is not None else (status.get("invoice_amount") or 0.0)
                status["remaining_amount"] = 0.0
            clean_status = {
                k: v for k, v in status.items()
                if k in ("id", "payment_status", "invoice_status", "invoice_number", "invoice_date", "paid_amount")
            }
            invoicetoadd_bulk.append(OrdersPaymentInvoiceInfo(**clean_status,order_id=data.id))
        
        self.session.add_all(invoicetoadd_bulk)
        
        purchase_type = data.logistic_info.get("purchase_type")
        parent_id = data.logistic_info.get("last_order_id")
        
        if purchase_type == PurchaseTypes.EXISTING_RENEWAL.value and parent_id:
            renewal = OrderRenewals(
                id=generate_uuid(),
                parent_order_id=parent_id,
                new_order_id=data.id
            )
            self.session.add(renewal)
        elif purchase_type == PurchaseTypes.EXISTING_ADD_ON.value and parent_id:
            parent_order_qry = await self.session.execute(select(Orders.quantity, Orders.unit_price).where(Orders.id == parent_id))
            parent_order_data = parent_order_qry.first()
            if parent_order_data:
                # Need remaining days, but since we are inserting, we can calculate it from the expected delivery date difference
                from core.utils.calculations import get_remaining_days
                from core.constants import DEFAULT_ADDON_YEAR
                
                cur_delivery = data.delivery_info.get("delivery_date")
                last_expiry_str = data.logistic_info.get("last_ord_expiry_date")
                
                remaining_d = 0
                if cur_delivery and last_expiry_str:
                    try:
                        cur_delivery_date = datetime.strptime(cur_delivery, "%Y-%m-%d").date()
                        last_expiry_date = datetime.strptime(last_expiry_str, "%Y-%m-%d").date()
                        expiry_date = last_expiry_date + timedelta(days=DEFAULT_ADDON_YEAR+1)
                        remaining_d = get_remaining_days(from_date=expiry_date, to_date=cur_delivery)
                    except Exception:
                        remaining_d = 0

                addon = OrderAddOns(
                    id=generate_uuid(),
                    parent_order_id=parent_id,
                    new_order_id=data.id,
                    base_quantity=parent_order_data[0],
                    addon_quantity=data.quantity,
                    base_price=parent_order_data[1],
                    addon_price=data.unit_price,
                    remaining_days=remaining_d
                )
                self.session.add(addon)

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
            
            from core.utils.calculations import get_remaining_days
            from core.constants import DEFAULT_ADDON_YEAR
            
            addons_to_insert = []
            renewals_to_insert = []
            for order in datas:
                purchase_type = order.logistic_info.get("purchase_type")
                parent_id = order.logistic_info.get("last_order_id")
                
                if purchase_type == PurchaseTypes.EXISTING_RENEWAL.value and parent_id:
                    renewals_to_insert.append(OrderRenewals(
                        id=generate_uuid(),
                        parent_order_id=parent_id,
                        new_order_id=order.id
                    ))
                elif purchase_type == PurchaseTypes.EXISTING_ADD_ON.value and parent_id:
                    parent_order_qry = await self.session.execute(select(Orders.quantity, Orders.unit_price).where(Orders.id == parent_id))
                    parent_order_data = parent_order_qry.first()
                    if parent_order_data:
                        cur_delivery = order.delivery_info.get("delivery_date")
                        last_expiry_str = order.logistic_info.get("last_ord_expiry_date")
                        
                        remaining_d = 0
                        if cur_delivery and last_expiry_str:
                            try:
                                cur_delivery_date = datetime.strptime(cur_delivery, "%Y-%m-%d").date()
                                last_expiry_date = datetime.strptime(last_expiry_str, "%Y-%m-%d").date()
                                expiry_date = last_expiry_date + timedelta(days=DEFAULT_ADDON_YEAR+1)
                                remaining_d = get_remaining_days(from_date=expiry_date, to_date=cur_delivery)
                            except Exception:
                                remaining_d = 0

                        addons_to_insert.append(OrderAddOns(
                            id=generate_uuid(),
                            parent_order_id=parent_id,
                            new_order_id=order.id,
                            base_quantity=parent_order_data[0],
                            addon_quantity=order.quantity,
                            base_price=parent_order_data[1],
                            addon_price=order.unit_price,
                            remaining_days=remaining_d
                        ))

            if renewals_to_insert:
                self.session.add_all(renewals_to_insert)
            if addons_to_insert:
                self.session.add_all(addons_to_insert)

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
            if status.get("payment_status") in ("FULL PAYMENT RECEIVED", "PAID"):
                status["paid_amount"] = status.get("paid_amount") if status.get("paid_amount") is not None else (status.get("invoice_amount") or 0.0)
                status["remaining_amount"] = 0.0
            clean_status = {
                k: v for k, v in status.items()
                if k in ("id", "payment_status", "invoice_status", "invoice_number", "invoice_date", "paid_amount")
            }
            invoicetoadd_bulk.append(OrdersPaymentInvoiceInfo(**clean_status,order_id=data.order_id))
        
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
        cursor=int(cursor)
        limit=int(limit)
        search_term = f"%{query.lower()}%"

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
            .join(OrderAddOns, OrderAddOns.new_order_id == Orders.id, isouter=True)
            .where(
                *conditions,
                *filters
            )
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

        from_date = None
        to_date = None
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

        if in_search and len(in_search)>0:
            orders_toquery=orders_toquery.where(Orders.id.in_(in_search))
            
        # Execute normal orders query
        queried_orders=(await self.session.execute(orders_toquery)).mappings().all()

        # Execute cart orders query
        from ..models.order import CartOrders, CartOrdersProduct, CartOrdersPaymentInvoiceInfo, CartOrdersAdditionalQuantity
        from infras.primary_db.repos.order_cart_repo import OrdersCartRepo
        
        cart_repo = OrdersCartRepo(session=self.session, user_role=self.user_role, cur_user_id=self.cur_user_id)
        
        cart_conditions = []
        cart_filters = []
        
        cart_conditions.append(
            or_(
                CartOrders.id.ilike(search_term),
                CartOrders.ui_id.ilike(search_term),
                CartOrders.distributor_id.ilike(search_term),
                Distributors.ui_id.ilike(search_term),
                Customers.name.ilike(search_term),
                Customers.email.ilike(search_term),
                Customers.mobile_number.ilike(search_term),
                CartOrders.logistic_info['purchase_type'].astext.ilike(search_term),
                CartOrders.logistic_info['renewal_type'].astext.ilike(search_term),
                Distributors.name.ilike(search_term),
                CartOrders.logistic_info['bill_to'].astext.ilike(search_term),
                CartOrders.logistic_info['distributor_type'].astext.ilike(search_term),
                exists().where(
                    and_(
                        CartOrdersPaymentInvoiceInfo.order_id == CartOrders.id,
                        CartOrdersPaymentInvoiceInfo.invoice_number.ilike(search_term)
                    )
                ),
                exists().where(
                    and_(
                        CartOrdersProduct.order_id == CartOrders.id,
                        exists().where(
                            and_(
                                Products.id == CartOrdersProduct.product_id,
                                or_(
                                    Products.name.ilike(search_term),
                                    Products.id.ilike(search_term),
                                    Products.ui_id.ilike(search_term),
                                    Products.product_type.ilike(search_term)
                                )
                            )
                        )
                    )
                )
            )
        )
        cart_conditions.append(CartOrders.is_deleted.is_(include_deleted))

        for key, value in filter.model_dump(mode='json').items():
            if value is None:
                continue

            if key == "payment_status":
                cart_filters.append(
                    exists().where(
                        and_(
                            CartOrdersPaymentInvoiceInfo.order_id == CartOrders.id,
                            CartOrdersPaymentInvoiceInfo.payment_status == value,
                            CartOrdersPaymentInvoiceInfo.invoice_status == InvoiceStatus.COMPLETED.value
                        )
                    )
                )

            elif key == "invoice_status":
                cart_filters.append(
                    exists().where(
                        and_(
                            CartOrdersPaymentInvoiceInfo.order_id == CartOrders.id,
                            CartOrdersPaymentInvoiceInfo.invoice_status == value
                        )
                    )
                )

            elif key != "date_filter" and key != "revenue_type":
                if key == "activation_status":
                    cart_filters.append(CartOrders.activated == value)
                elif key == "distributor_id":
                    cart_filters.append(CartOrders.distributor_id == value)
                elif key == "customer_id":
                    cart_filters.append(CartOrders.customer_id == value)
                elif key == "product_id":
                    cart_filters.append(
                        exists().where(
                            and_(
                                CartOrdersProduct.order_id == CartOrders.id,
                                CartOrdersProduct.product_id == value
                            )
                        )
                    )
                elif key == "owner_name":
                    cart_filters.append(Customers.owner == value)
                elif key == "product_type":
                    cart_filters.append(
                        exists().where(
                            and_(
                                CartOrdersProduct.order_id == CartOrders.id,
                                exists().where(
                                    and_(
                                        Products.id == CartOrdersProduct.product_id,
                                        Products.product_type == value
                                    )
                                )
                            )
                        )
                    )
                elif key == "purchase_type":
                    cart_filters.append(CartOrders.logistic_info['purchase_type'].astext == value)
                elif key == "renewal_type":
                    cart_filters.append(CartOrders.logistic_info['renewal_type'].astext == value)
                elif key == "distributor_type":
                    cart_filters.append(CartOrders.logistic_info['distributor_type'].astext == value)

        cart_toquery = (
            select(
                *cart_repo.orders_cols
            )
            .join(Distributors, Distributors.id == CartOrders.distributor_id, isouter=True)
            .join(Customers, Customers.id == CartOrders.customer_id, isouter=True)
            .join(cart_repo.product_subquery, cart_repo.product_subquery.c.order_id == CartOrders.id, isouter=True)
            .join(cart_repo.payment_subquery, cart_repo.payment_subquery.c.order_id == CartOrders.id, isouter=True)
            .where(
                *cart_conditions,
                *cart_filters
            )
        )

        cart_date_tofilter = None
        if date_by == OrderFilterDateByEnum.REQUESTED_DATE.value:
            cart_date_tofilter = cast(CartOrders.delivery_info["requested_date"].astext, Date)
        elif date_by == OrderFilterDateByEnum.ACTIVATION_DATE.value: 
            cart_date_tofilter = cast(CartOrders.delivery_info["delivery_date"].astext, Date)
        elif date_by == OrderFilterDateByEnum.CREATED_DATE.value:
            cart_date_tofilter = cast(CartOrders.created_at, Date)

        if cart_date_tofilter is not None and from_date is not None and to_date is not None:
            cart_toquery = cart_toquery.where(
                and_(
                    cart_date_tofilter >= from_date,
                    cart_date_tofilter <= to_date
                )
            )

        if active:
            cart_delivery_date = cast(CartOrders.delivery_info["delivery_date"].astext, Date)
            cart_active_condition = and_(
                cart_delivery_date >= func.current_date() - text("INTERVAL '365 days'"),
                CartOrders.activated.is_(True)
            )
            cart_toquery = cart_toquery.where(cart_active_condition)

        if in_search and len(in_search) > 0:
            cart_toquery = cart_toquery.where(CartOrders.id.in_(in_search))

        cart_orders_results = (await self.session.execute(cart_toquery)).mappings().all()

        # Map both standard and cart orders to a unified format
        mapped_normal = []
        for row in queried_orders:
            o = dict(row)
            o["is_cart"] = False
            o["products"] = [{
                "id": o.get("product_id"),
                "product_id": o.get("product_id"),
                "name": o.get("product_name"),
                "price": o.get("product_price"),
                "quantity": o.get("quantity"),
                "unit_price": o.get("unit_price"),
                "additional_price": o.get("additional_price"),
                "additional_discount": o.get("additional_discount"),
                "discount_id": o.get("discount_id"),
                "vendor_commision": o.get("vendor_commision"),
                "customer_price": o.get("customer_price"),
                "distributor_price": o.get("distributor_price"),
                "vendor_total_price": o.get("vendor_total_price"),
                "profit_loss": o.get("profit_loss"),
            }]
            disc_val = o.get("distributor_discount")
            if isinstance(disc_val, dict):
                o["distributor_discount"] = disc_val
            elif isinstance(disc_val, str) and disc_val.strip().startswith("{"):
                import json
                try:
                    o["distributor_discount"] = json.loads(disc_val)
                except Exception:
                    o["distributor_discount"] = {"discount": disc_val}
            else:
                o["distributor_discount"] = {"discount": str(disc_val or "0")}
            o["total_price"] = o.get("customer_price") or 0.0
            o["total_license"] = o.get("quantity") or 0
            
            # Map Add-On specifically if present
            if o.get("addon_quantity") is not None:
                o["addon_info"] = {
                    "base_quantity": o.get("addon_base_quantity"),
                    "addon_quantity": o.get("addon_quantity"),
                    "base_price": o.get("addon_base_price"),
                    "addon_price": o.get("addon_price"),
                    "remaining_days": o.get("addon_remaining_days"),
                }
                
            mapped_normal.append(o)

        mapped_cart = []
        for row in cart_orders_results:
            o = cart_repo._map_single_cart_order(row)
            products_list = o.get("products") or []
            
            product_names = [p.get("name") or p.get("product_name") or "" for p in products_list]
            product_names = [name for name in product_names if name]
            o["product_name"] = ", ".join(product_names) if product_names else "Multiple Products"
            
            product_ui_ids = [p.get("product_ui_id") or p.get("ui_id") or "" for p in products_list]
            product_ui_ids = [ui for ui in product_ui_ids if ui]
            o["product_ui_id"] = ", ".join(product_ui_ids) if product_ui_ids else "MULT-PROD"
            
            first_product_discount = "0"
            if products_list:
                first_p = products_list[0]
                disc_obj = first_p.get("discount")
                if isinstance(disc_obj, dict):
                    first_product_discount = str(disc_obj.get("discount") or "0")
                else:
                    first_product_discount = str(first_p.get("additional_discount") or "0")
            o["distributor_discount"] = {"discount": first_product_discount}
            o["customer_email"] = o.get("customer_email") or ""
            mapped_cart.append(o)

        combined_mapped = mapped_normal + mapped_cart

        # Filter by revenue type in Python
        if getattr(filter, 'revenue_type', None):
            revenue = filter.revenue_type.value if isinstance(filter.revenue_type, OrderFilterRevenueEnum) else filter.revenue_type
            if revenue == OrderFilterRevenueEnum.PROFIT.value:
                combined_mapped = [o for o in combined_mapped if (o.get("profit_loss") or 0.0) > 0]
            elif revenue == OrderFilterRevenueEnum.LOSS.value:
                combined_mapped = [o for o in combined_mapped if (o.get("profit_loss") or 0.0) < 0]

        # Sort by created_at descending
        def get_created_at(order):
            c_at = order.get("created_at") or order.get("order_created_at")
            if c_at is None:
                return datetime.min
            if isinstance(c_at, str):
                try:
                    dt = datetime.fromisoformat(c_at.replace("Z", "+00:00"))
                    return dt.replace(tzinfo=None)
                except Exception:
                    try:
                        dt = datetime.strptime(c_at, "%Y-%m-%d")
                        return dt.replace(tzinfo=None)
                    except Exception:
                        return datetime.min
            if isinstance(c_at, (datetime, date)):
                if isinstance(c_at, date) and not isinstance(c_at, datetime):
                    return datetime.combine(c_at, datetime.min.time())
                return c_at.replace(tzinfo=None)
            return datetime.min

        combined_mapped.sort(key=get_created_at, reverse=True)

        # 3. Calculate statistics over the combined dataset
        total_revenue = 0.0
        distributor_value = 0.0
        total_license = 0
        total_orders = len(combined_mapped)
        order_value = 0.0
        not_activated = 0
        
        pending_invoice = 0
        tds_pendings = 0
        tot_pending_dues = 0
        vendor_value = 0.0
        
        not_paid_pendings = 0
        gst_pendings = 0
        half_pendings = 0
        short_pendings = 0
        
        not_paid_amounts = 0.0
        tds_amounts = 0.0
        gst_amounts = 0.0
        half_amounts = 0.0
        short_amounts = 0.0
        pending_amounts = 0.0
        tot_pending_amounts = 0.0
        
        distributor_pivot = {}

        for o in combined_mapped:
            order_total_price = o.get("customer_price") or 0.0
            order_distributor_price = o.get("distributor_price") or 0.0
            order_vendor_total_price = o.get("vendor_total_price") or 0.0
            order_profit_loss = o.get("profit_loss") or 0.0
            order_license_val = o.get("quantity") or 0
            purchase_type = (o.get("logistic_info") or {}).get("purchase_type") or ""
            
            total_revenue += order_profit_loss
            distributor_value += order_distributor_price
            total_license += order_license_val
            order_value += order_total_price
            vendor_value += order_vendor_total_price
            
            if not o.get("activated"):
                not_activated += 1
                
            invoices = o.get("status_info") or []
            for inv in invoices:
                invoice_status = inv.get("invoice_status")
                payment_status = inv.get("payment_status")
                paid_amount = float(inv.get("paid_amount") or 0)
                
                cust_total_inc_gst = round(order_total_price * 1.18)
                count = len(invoices)
                per_invoice_amt = round(cust_total_inc_gst / count) if count > 0 else 0
                
                remaining_bal = max(per_invoice_amt - paid_amount, 0)
                if payment_status in (PaymentStatus.PAID.value, PaymentStatus.FULL_PAYMENT_RECEIVED.value):
                    remaining_bal = 0.0
                
                if invoice_status == "COMPLETED":
                    if payment_status == PaymentStatus.NOT_PAID.value:
                        not_paid_pendings += 1
                        not_paid_amounts += remaining_bal
                    elif payment_status == PaymentStatus.GST_PENDING.value:
                        gst_pendings += 1
                        gst_amounts += remaining_bal
                    elif payment_status == PaymentStatus.HALF_PAYMENT_RECEIVED.value:
                        half_pendings += 1
                        half_amounts += remaining_bal
                    elif payment_status == PaymentStatus.SHORT_PAYMENT_RECEIVED.value:
                        short_pendings += 1
                        short_amounts += remaining_bal
                    elif payment_status == PaymentStatus.TDS_PENDING.value:
                        tds_pendings += 1
                        tds_amounts += remaining_bal
                elif invoice_status == "PENDING" or invoice_status == "INCOMPLETED":
                    pending_invoice += 1
                    pending_amounts += per_invoice_amt
                    
            # Pivot group
            dist_id = o.get("distributor_id")
            if dist_id:
                if dist_id not in distributor_pivot:
                    distributor_pivot[dist_id] = {
                        "distributor_id": dist_id,
                        "existing_renewal": 0.0,
                        "new_logo_renewal": 0.0,
                        "net_new_customer": 0.0,
                        "existing_add_on": 0.0
                    }
                p_pivot = distributor_pivot[dist_id]
                if purchase_type == "EXISTING-RENEWAL":
                    p_pivot["existing_renewal"] += order_total_price
                elif purchase_type == "NEW-LOGO-RENEWAL":
                    p_pivot["new_logo_renewal"] += order_total_price
                elif purchase_type == "NET-NEW-CUSTOMER":
                    p_pivot["net_new_customer"] += order_total_price
                elif purchase_type == "EXISTING-ADD-ON":
                    p_pivot["existing_add_on"] += order_total_price

        purchase_stats = list(distributor_pivot.values())
        tot_pending_amounts = not_paid_amounts + gst_amounts + half_amounts + short_amounts + tds_amounts
        tot_pending_dues = not_paid_pendings + gst_pendings + half_pendings + short_pendings + tds_pendings

        stats = {
            "total_revenue": total_revenue,
            "distributor_value": distributor_value,
            "total_license": total_license,
            "total_orders": total_orders,
            "order_value": order_value,
            "not_activated": not_activated,
            "pending_invoice": pending_invoice,
            "tds_pendings": tds_pendings,
            "tot_pending_dues": tot_pending_dues,
            "vendor_value": vendor_value,
            "not_paid_pendings": not_paid_pendings,
            "gst_pendings": gst_pendings,
            "half_pendings": half_pendings,
            "short_pendings": short_pendings,
            "not_paid_amounts": not_paid_amounts,
            "tds_amounts": tds_amounts,
            "gst_amounts": gst_amounts,
            "half_amounts": half_amounts,
            "short_amounts": short_amounts,
            "pending_amounts": pending_amounts,
            "tot_pending_amounts": tot_pending_amounts,
        }

        # 4. Paginate
        start_idx = 0 if cursor == 1 else cursor
        end_idx = start_idx + limit
        paginated_orders = combined_mapped[start_idx:end_idx]

        return {
            **stats,
            "purchase_stats": purchase_stats,
            "total_pages": ceil(len(combined_mapped) / limit) if limit > 0 else 1,
            "next_cursor": start_idx + len(paginated_orders) if (start_idx + len(paginated_orders) < len(combined_mapped)) else None,
            "orders": paginated_orders
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
            .join(OrderAddOns, OrderAddOns.new_order_id == Orders.id, isouter=True)
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
            .join(OrderAddOns, OrderAddOns.new_order_id == Orders.id, isouter=True)
            .where(or_(Orders.id==order_id,Orders.ui_id==order_id),Orders.is_deleted==include_delete)
        )).mappings().one_or_none()

        if queried_orders is not None:
            o = dict(queried_orders)
            o["is_cart"] = False
            
            # Fetch sum of registered addon quantities on this parent order (both placed standard addons and draft cart addons)
            addon_sum_query = select(func.coalesce(func.sum(OrderAddOns.addon_quantity), 0)).where(OrderAddOns.parent_order_id == o.get("id"))
            total_addon_qty = (await self.session.execute(addon_sum_query)).scalar_one()
            
            from ..models.order import CartOrders, CartOrdersProduct
            draft_sum_query = (
                select(func.coalesce(func.sum(CartOrdersProduct.quantity), 0))
                .join(CartOrders, CartOrders.id == CartOrdersProduct.order_id)
                .where(
                    CartOrders.logistic_info['last_order_id'].astext == o.get("id"),
                    CartOrders.logistic_info['purchase_type'].astext == 'EXISTING-ADD-ON',
                    CartOrders.is_deleted == False
                )
            )
            draft_addon_qty = (await self.session.execute(draft_sum_query)).scalar_one()
            
            o["total_addon_quantity"] = total_addon_qty + draft_addon_qty
            
            o["products"] = [{
                "id": o.get("product_id"),
                "product_id": o.get("product_id"),
                "name": o.get("product_name"),
                "price": o.get("product_price"),
                "quantity": o.get("quantity"),
                "unit_price": o.get("unit_price"),
                "additional_price": o.get("additional_price"),
                "additional_discount": o.get("additional_discount"),
                "discount_id": o.get("discount_id"),
                "vendor_commision": o.get("vendor_commision"),
                "customer_price": o.get("customer_price"),
                "distributor_price": o.get("distributor_price"),
                "vendor_total_price": o.get("vendor_total_price"),
                "profit_loss": o.get("profit_loss"),
            }]
            disc_val = o.get("distributor_discount")
            if isinstance(disc_val, dict):
                o["distributor_discount"] = disc_val
            elif isinstance(disc_val, str) and disc_val.strip().startswith("{"):
                import json
                try:
                    o["distributor_discount"] = json.loads(disc_val)
                except Exception:
                    o["distributor_discount"] = {"discount": disc_val}
            else:
                o["distributor_discount"] = {"discount": str(disc_val or "0")}
            o["total_price"] = o.get("customer_price") or 0.0
            o["total_license"] = o.get("quantity") or 0
            return {'order': o}

        # Fallback to CartOrders
        from ..models.order import CartOrders, CartOrdersProduct, CartOrdersPaymentInvoiceInfo, CartOrderAddOns
        from infras.primary_db.repos.order_cart_repo import OrdersCartRepo
        
        cart_repo = OrdersCartRepo(session=self.session, user_role=self.user_role, cur_user_id=self.cur_user_id)
        
        cart_toquery = (
            select(
                *cart_repo.orders_cols
            )
            .join(Distributors, Distributors.id == CartOrders.distributor_id, isouter=True)
            .join(Customers, Customers.id == CartOrders.customer_id, isouter=True)
            .join(cart_repo.product_subquery, cart_repo.product_subquery.c.order_id == CartOrders.id, isouter=True)
            .join(cart_repo.payment_subquery, cart_repo.payment_subquery.c.order_id == CartOrders.id, isouter=True)
            .where(
                or_(CartOrders.id == order_id, CartOrders.ui_id == order_id),
                CartOrders.is_deleted == include_delete
            )
        )
        
        row = (await self.session.execute(cart_toquery)).mappings().one_or_none()
        if row is not None:
            o = cart_repo._map_single_cart_order(row)
            
            # Fetch sum of registered cart addon quantities on this parent cart order (both placed standard addons and draft cart addons)
            cart_addon_sum_query = select(func.coalesce(func.sum(CartOrderAddOns.addon_quantity), 0)).where(CartOrderAddOns.parent_cart_order_id == o.get("id"))
            total_cart_addon_qty = (await self.session.execute(cart_addon_sum_query)).scalar_one()
            
            from ..models.order import CartOrders, CartOrdersProduct
            draft_sum_query = (
                select(func.coalesce(func.sum(CartOrdersProduct.quantity), 0))
                .join(CartOrders, CartOrders.id == CartOrdersProduct.order_id)
                .where(
                    CartOrders.logistic_info['last_order_id'].astext == o.get("id"),
                    CartOrders.logistic_info['purchase_type'].astext == 'EXISTING-ADD-ON',
                    CartOrders.is_deleted == False
                )
            )
            draft_addon_qty = (await self.session.execute(draft_sum_query)).scalar_one()
            
            o["total_addon_quantity"] = total_cart_addon_qty + draft_addon_qty
            
            products_list = o.get("products") or []
            
            product_names = [p.get("name") or p.get("product_name") or "" for p in products_list]
            product_names = [name for name in product_names if name]
            o["product_name"] = ", ".join(product_names) if product_names else "Multiple Products"
            
            product_ui_ids = [p.get("product_ui_id") or p.get("ui_id") or "" for p in products_list]
            product_ui_ids = [ui for ui in product_ui_ids if ui]
            o["product_ui_id"] = ", ".join(product_ui_ids) if product_ui_ids else "MULT-PROD"
            
            first_product_discount = "0"
            if products_list:
                first_p = products_list[0]
                disc_obj = first_p.get("discount")
                if isinstance(disc_obj, dict):
                    first_product_discount = str(disc_obj.get("discount") or "0")
                else:
                    first_product_discount = str(first_p.get("additional_discount") or "0")
            o["distributor_discount"] = {"discount": first_product_discount}
            o["total_price"] = o.get("customer_price") or 0.0
            o["total_license"] = o.get("quantity") or 0
            o["customer_email"] = o.get("customer_email") or ""
            
            return {'order': o}

        return {'order': None}
        
    
    async def get_by_customer_id(self,customer_id:str,cursor:int,limit:int):
        date_expr=func.date(func.timezone("Asia/Kolkata",Orders.created_at))
        cursor=int(cursor)
        limit=int(limit)
        
        # Standard orders query for customer
        orders_toquery = (
            select(
                *self.orders_cols,
                date_expr.label("order_created_at")
            )
            .join(self.subquery, self.subquery.c.order_id == Orders.id, isouter=True)
            .join(Products,Products.id==Orders.product_id,isouter=True)
            .join(Customers,Customers.id==Orders.customer_id,isouter=True)
            .join(Distributors,Distributors.id==Orders.distributor_id,isouter=True)
            .where(
                Orders.customer_id==customer_id,
                Orders.is_deleted==False
            )
        )
        
        queried_orders = (await self.session.execute(orders_toquery)).mappings().all()

        # Cart orders query for customer
        from ..models.order import CartOrders, CartOrdersProduct, CartOrdersPaymentInvoiceInfo, CartOrdersAdditionalQuantity
        from infras.primary_db.repos.order_cart_repo import OrdersCartRepo
        
        cart_repo = OrdersCartRepo(session=self.session, user_role=self.user_role, cur_user_id=self.cur_user_id)
        
        cart_toquery = (
            select(
                *cart_repo.orders_cols
            )
            .join(Distributors, Distributors.id == CartOrders.distributor_id, isouter=True)
            .join(Customers, Customers.id == CartOrders.customer_id, isouter=True)
            .join(cart_repo.product_subquery, cart_repo.product_subquery.c.order_id == CartOrders.id, isouter=True)
            .join(cart_repo.payment_subquery, cart_repo.payment_subquery.c.order_id == CartOrders.id, isouter=True)
            .where(
                CartOrders.customer_id==customer_id,
                CartOrders.is_deleted==False
            )
        )
        
        cart_orders_results = (await self.session.execute(cart_toquery)).mappings().all()

        # Map normal orders
        mapped_normal = []
        for row in queried_orders:
            o = dict(row)
            o["is_cart"] = False
            o["products"] = [{
                "id": o.get("product_id"),
                "product_id": o.get("product_id"),
                "name": o.get("product_name"),
                "price": o.get("product_price"),
                "quantity": o.get("quantity"),
                "unit_price": o.get("unit_price"),
                "additional_price": o.get("additional_price"),
                "additional_discount": o.get("additional_discount"),
                "discount_id": o.get("discount_id"),
                "vendor_commision": o.get("vendor_commision"),
                "customer_price": o.get("customer_price"),
                "distributor_price": o.get("distributor_price"),
                "vendor_total_price": o.get("vendor_total_price"),
                "profit_loss": o.get("profit_loss"),
            }]
            disc_val = o.get("distributor_discount")
            if isinstance(disc_val, dict):
                o["distributor_discount"] = disc_val
            elif isinstance(disc_val, str) and disc_val.strip().startswith("{"):
                import json
                try:
                    o["distributor_discount"] = json.loads(disc_val)
                except Exception:
                    o["distributor_discount"] = {"discount": disc_val}
            else:
                o["distributor_discount"] = {"discount": str(disc_val or "0")}
            o["total_price"] = o.get("customer_price") or 0.0
            o["total_license"] = o.get("quantity") or 0
            mapped_normal.append(o)

        # Map cart orders
        mapped_cart = []
        for row in cart_orders_results:
            o = cart_repo._map_single_cart_order(row)
            products_list = o.get("products") or []
            
            product_names = [p.get("name") or p.get("product_name") or "" for p in products_list]
            product_names = [name for name in product_names if name]
            o["product_name"] = ", ".join(product_names) if product_names else "Multiple Products"
            
            product_ui_ids = [p.get("product_ui_id") or p.get("ui_id") or "" for p in products_list]
            product_ui_ids = [ui for ui in product_ui_ids if ui]
            o["product_ui_id"] = ", ".join(product_ui_ids) if product_ui_ids else "MULT-PROD"
            
            first_product_discount = "0"
            if products_list:
                first_p = products_list[0]
                disc_obj = first_p.get("discount")
                if isinstance(disc_obj, dict):
                    first_product_discount = str(disc_obj.get("discount") or "0")
                else:
                    first_product_discount = str(first_p.get("additional_discount") or "0")
            o["distributor_discount"] = {"discount": first_product_discount}
            o["customer_email"] = o.get("customer_email") or ""
            mapped_cart.append(o)

        combined_mapped = mapped_normal + mapped_cart

        # Sort by created_at descending
        def get_created_at(order):
            c_at = order.get("created_at") or order.get("order_created_at")
            if c_at is None:
                return datetime.min
            if isinstance(c_at, str):
                try:
                    dt = datetime.fromisoformat(c_at.replace("Z", "+00:00"))
                    return dt.replace(tzinfo=None)
                except Exception:
                    try:
                        dt = datetime.strptime(c_at, "%Y-%m-%d")
                        return dt.replace(tzinfo=None)
                    except Exception:
                        return datetime.min
            if isinstance(c_at, (datetime, date)):
                if isinstance(c_at, date) and not isinstance(c_at, datetime):
                    return datetime.combine(c_at, datetime.min.time())
                return c_at.replace(tzinfo=None)
            return datetime.min

        combined_mapped.sort(key=get_created_at, reverse=True)

        # Calculate customer-specific stats
        total_revenue = 0.0
        distributor_value = 0.0
        total_license = 0
        total_orders = len(combined_mapped)
        order_value = 0.0
        not_activated = 0
        
        pending_invoice = 0
        vendor_value = 0.0
        pending_amounts = 0.0
        tot_pending_amounts = 0.0
        tot_pending_dues = 0

        for o in combined_mapped:
            order_total_price = o.get("customer_price") or 0.0
            order_distributor_price = o.get("distributor_price") or 0.0
            order_vendor_total_price = o.get("vendor_total_price") or 0.0
            order_profit_loss = o.get("profit_loss") or 0.0
            order_license_val = o.get("quantity") or 0
            
            total_revenue += order_profit_loss
            distributor_value += order_distributor_price
            total_license += order_license_val
            order_value += order_total_price
            vendor_value += order_vendor_total_price
            
            if not o.get("activated"):
                not_activated += 1
                
            invoices = o.get("status_info") or []
            for inv in invoices:
                invoice_status = inv.get("invoice_status")
                payment_status = inv.get("payment_status")
                paid_amount = float(inv.get("paid_amount") or 0)
                
                cust_total_inc_gst = round(order_total_price * 1.18)
                count = len(invoices)
                per_invoice_amt = round(cust_total_inc_gst / count) if count > 0 else 0
                
                remaining_bal = max(per_invoice_amt - paid_amount, 0)
                if payment_status in (PaymentStatus.PAID.value, PaymentStatus.FULL_PAYMENT_RECEIVED.value):
                    remaining_bal = 0.0
                
                if invoice_status == "COMPLETED":
                    if payment_status != PaymentStatus.PAID.value and payment_status != PaymentStatus.FULL_PAYMENT_RECEIVED.value:
                        tot_pending_dues += 1
                        tot_pending_amounts += remaining_bal
                elif invoice_status == "PENDING" or invoice_status == "INCOMPLETED":
                    pending_invoice += 1
                    pending_amounts += per_invoice_amt

        orders_infos = {
            "total_revenue": total_revenue,
            "distributor_value": distributor_value,
            "total_license": total_license,
            "total_orders": total_orders,
            "order_value": order_value,
            "not_activated": not_activated,
            "pending_invoice": pending_invoice,
            "vendor_value": vendor_value,
            "pending_amounts": pending_amounts,
            "tot_pending_amounts": tot_pending_amounts,
            "tot_pending_dues": tot_pending_dues
        }

        # Paginate
        start_idx = 0 if cursor == 1 else cursor
        end_idx = start_idx + limit
        paginated_orders = combined_mapped[start_idx:end_idx]

        return {
            **orders_infos,
            'orders': paginated_orders,
            'total_pages': ceil(len(combined_mapped) / limit) if limit > 0 else 1,
            'next_cursor': start_idx + len(paginated_orders) if (start_idx + len(paginated_orders) < len(combined_mapped)) else None
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
        
    async def _get_filtered_cart_orders(self, from_date, to_date, owner_name=None, date_by=None, distributor_id=None):
        from infras.primary_db.repos.order_cart_repo import OrdersCartRepo
        from core.data_formats.enums.order_enums import OrderFilterDateByEnum
        
        cart_repo = OrdersCartRepo(session=self.session, user_role=self.user_role, cur_user_id=self.cur_user_id)
        
        # --- Date field to filter on ---
        date_by_val = None
        if date_by:
            date_by_val = date_by.value if hasattr(date_by, 'value') else date_by

        if date_by_val == OrderFilterDateByEnum.REQUESTED_DATE.value:
            date_field = cast(CartOrders.delivery_info["requested_date"].astext, Date)
        elif date_by_val == OrderFilterDateByEnum.CREATED_DATE.value:
            date_field = cast(CartOrders.created_at, Date)
        else:
            # Default: ACTIVATION_DATE (delivery_date)
            date_field = cast(CartOrders.delivery_info["delivery_date"].astext, Date)
            
        conditions = [CartOrders.is_deleted == False]
        if from_date:
            conditions.append(date_field >= from_date)
        if to_date:
            conditions.append(date_field <= to_date)
        if owner_name and owner_name.upper() != 'ALL':
            conditions.append(Customers.owner == owner_name)
        if distributor_id and distributor_id.upper() != 'ALL':
            conditions.append(CartOrders.distributor_id == distributor_id)
            
        stmt = (
            select(
                *cart_repo.orders_cols
            )
            .join(Distributors, Distributors.id == CartOrders.distributor_id, isouter=True)
            .join(Customers, Customers.id == CartOrders.customer_id, isouter=True)
            .join(cart_repo.product_subquery, cart_repo.product_subquery.c.order_id == CartOrders.id, isouter=True)
            .join(cart_repo.payment_subquery, cart_repo.payment_subquery.c.order_id == CartOrders.id, isouter=True)
            .where(*conditions)
            .order_by(desc(CartOrders.created_at))
        )
        
        results = (await self.session.execute(stmt)).mappings().all()
        return [cart_repo._map_single_cart_order(row) for row in results]

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
        ]
        
        if from_date:
            conditions.append(date_field >= from_date)
        if to_date:
            conditions.append(date_field <= to_date)

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
        #    Value = customer_final_price
        payment_pending_val = func.coalesce(func.sum(
            case(
                (
                    and_(
                        Orders.activated == True,
                        func.coalesce(invoice_agg_subq.c.has_completed_invoice, False) == True,
                    ),
                    customer_final_price
                ),
                else_=0
            )
        ), 0)

        # 3) PO received, activation need to done:
        #    activated=False
        po_received_activation_pending = func.coalesce(func.sum(
            case(
                (
                    Orders.activated == False,
                    customer_final_price
                ),
                else_=0
            )
        ), 0)

        # --- Product type label ---
        product_type_label = func.coalesce(
            func.nullif(func.trim(Products.product_type), ''),
            'Others'
        ).label("product_type")

        # --- Main aggregation query ---
        report_stmt = (
            select(
                owner_label,
                product_type_label,
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
            .group_by(owner_label, product_type_label)
            .order_by(owner_label, product_type_label)
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
                                Orders.activated == True,
                                func.coalesce(invoice_agg_subq.c.has_completed_invoice, False) == True,
                            ),
                            customer_final_price
                        ),
                        else_=0
                    )
                ), 0), Numeric), 2).label("payment_pending"),
                func.round(cast(func.coalesce(func.sum(
                    case(
                        (
                            Orders.activated == False,
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

        owners_dict = {}
        for row in owner_rows:
            o_name = row["owner_name"]
            p_type = row["product_type"]
            
            if o_name not in owners_dict:
                owners_dict[o_name] = {
                    "owner_name": o_name,
                    "activation_done_invoice_pending": 0.0,
                    "payment_pending": 0.0,
                    "po_received_activation_pending": 0.0,
                    "grand_total": 0.0,
                    "product_breakdown": {}
                }
            
            owners_dict[o_name]["activation_done_invoice_pending"] += float(row["activation_done_invoice_pending"] or 0)
            owners_dict[o_name]["payment_pending"] += float(row["payment_pending"] or 0)
            owners_dict[o_name]["po_received_activation_pending"] += float(row["po_received_activation_pending"] or 0)
            owners_dict[o_name]["grand_total"] += float(row["grand_total"] or 0)
            
            if p_type not in owners_dict[o_name]["product_breakdown"]:
                owners_dict[o_name]["product_breakdown"][p_type] = {
                    "activation_done_invoice_pending": 0.0,
                    "payment_pending": 0.0,
                    "po_received_activation_pending": 0.0,
                    "grand_total": 0.0
                }
            
            owners_dict[o_name]["product_breakdown"][p_type]["activation_done_invoice_pending"] += float(row["activation_done_invoice_pending"] or 0)
            owners_dict[o_name]["product_breakdown"][p_type]["payment_pending"] += float(row["payment_pending"] or 0)
            owners_dict[o_name]["product_breakdown"][p_type]["po_received_activation_pending"] += float(row["po_received_activation_pending"] or 0)
            owners_dict[o_name]["product_breakdown"][p_type]["grand_total"] += float(row["grand_total"] or 0)

        # --- Retrieve and aggregate Cart Orders ---
        cart_mapped_orders = await self._get_filtered_cart_orders(
            from_date=from_date,
            to_date=to_date,
            owner_name=owner_name,
            date_by=date_by
        )
        
        for o in cart_mapped_orders:
            owner_name_key = o.get("owner_name") or "Others"
            if owner_name_key not in owners_dict:
                owners_dict[owner_name_key] = {
                    "owner_name": owner_name_key,
                    "activation_done_invoice_pending": 0.0,
                    "payment_pending": 0.0,
                    "po_received_activation_pending": 0.0,
                    "grand_total": 0.0,
                    "product_breakdown": {}
                }
                
            invoices = o.get("status_info") or []
            has_completed_invoice = any(inv.get("invoice_status") == "COMPLETED" for inv in invoices)
            all_invoices_incompleted = all(inv.get("invoice_status") == "INCOMPLETED" for inv in invoices)
            
            products_list = o.get("products") or []
            
            for p in products_list:
                p_price = float(p.get("customer_price") or 0.0)
                p_type = p.get("product_type") or "Mixed"
                
                if p_type not in owners_dict[owner_name_key]["product_breakdown"]:
                    owners_dict[owner_name_key]["product_breakdown"][p_type] = {
                        "activation_done_invoice_pending": 0.0,
                        "payment_pending": 0.0,
                        "po_received_activation_pending": 0.0,
                        "grand_total": 0.0
                    }
                    
                val_1 = val_2 = val_3 = 0.0
                
                if o.get("activated") == True and all_invoices_incompleted:
                    val_1 = p_price
                if o.get("activated") == True and has_completed_invoice:
                    val_2 = p_price
                if o.get("activated") == False:
                    val_3 = p_price
                    
                owners_dict[owner_name_key]["activation_done_invoice_pending"] += val_1
                owners_dict[owner_name_key]["payment_pending"] += val_2
                owners_dict[owner_name_key]["po_received_activation_pending"] += val_3
                owners_dict[owner_name_key]["grand_total"] += val_1 + val_2 + val_3
                
                owners_dict[owner_name_key]["product_breakdown"][p_type]["activation_done_invoice_pending"] += val_1
                owners_dict[owner_name_key]["product_breakdown"][p_type]["payment_pending"] += val_2
                owners_dict[owner_name_key]["product_breakdown"][p_type]["po_received_activation_pending"] += val_3
                owners_dict[owner_name_key]["product_breakdown"][p_type]["grand_total"] += val_1 + val_2 + val_3

                grand_total["activation_done_invoice_pending"] += val_1
                grand_total["payment_pending"] += val_2
                grand_total["po_received_activation_pending"] += val_3
                grand_total["grand_total"] += val_1 + val_2 + val_3

        owners_data = sorted(list(owners_dict.values()), key=lambda x: x["owner_name"])
        
        for owner in owners_data:
            owner["activation_done_invoice_pending"] = round(owner["activation_done_invoice_pending"], 2)
            owner["payment_pending"] = round(owner["payment_pending"], 2)
            owner["po_received_activation_pending"] = round(owner["po_received_activation_pending"], 2)
            owner["grand_total"] = round(owner["grand_total"], 2)
            for p_type, breakdown in owner["product_breakdown"].items():
                breakdown["activation_done_invoice_pending"] = round(breakdown["activation_done_invoice_pending"], 2)
                breakdown["payment_pending"] = round(breakdown["payment_pending"], 2)
                breakdown["po_received_activation_pending"] = round(breakdown["po_received_activation_pending"], 2)
                breakdown["grand_total"] = round(breakdown["grand_total"], 2)
        
        grand_total["activation_done_invoice_pending"] = round(grand_total["activation_done_invoice_pending"], 2)
        grand_total["payment_pending"] = round(grand_total["payment_pending"], 2)
        grand_total["po_received_activation_pending"] = round(grand_total["po_received_activation_pending"], 2)
        grand_total["grand_total"] = round(grand_total["grand_total"], 2)

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

        if date_by_val == OrderFilterDateByEnum.ACTIVATION_DATE.value:
            date_field = cast(Orders.delivery_info["delivery_date"].astext, Date)
        elif date_by_val == OrderFilterDateByEnum.REQUESTED_DATE.value:
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
            OrdersPaymentInvoiceInfo.invoice_status == InvoiceStatus.COMPLETED.value,
            OrdersPaymentInvoiceInfo.payment_status.notin_([
                PaymentStatus.PAID.value,
                PaymentStatus.FULL_PAYMENT_RECEIVED.value
            ]),
        ]

        if from_date:
            conditions.append(date_field >= from_date)
        if to_date:
            conditions.append(date_field <= to_date)

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

        # --- Retrieve and process Cart Orders ---
        cart_mapped_orders = await self._get_filtered_cart_orders(
            from_date=from_date,
            to_date=to_date,
            owner_name=owner_name,
            date_by=date_by
        )

        from datetime import date, datetime
        today = date.today()

        cart_owner_aggs = {}
        for o in cart_mapped_orders:
            owner = o.get("owner_name") or "Others"
            invoices = o.get("status_info") or []
            
            # 1. Total invoices and matching completed pending invoices
            total_invoices_count = len(invoices)
            matching_completed_pending_invoices = []
            for inv in invoices:
                if inv.get("invoice_status") == "COMPLETED" and inv.get("payment_status") not in ("PAID", "FULL PAYMENT RECEIVED"):
                    # Apply min_days_pending filter if applicable
                    inv_date_str = inv.get("invoice_date")
                    days_p = 0
                    if inv_date_str:
                        if isinstance(inv_date_str, (datetime, date)):
                            inv_date = inv_date_str if isinstance(inv_date_str, date) else inv_date_str.date()
                        else:
                            try:
                                inv_date = datetime.strptime(str(inv_date_str)[:10], "%Y-%m-%d").date()
                            except Exception:
                                inv_date = None
                        if inv_date:
                            days_p = max((today - inv_date).days, 0)
                    if min_days_pending is not None and min_days_pending > 0 and days_p < min_days_pending:
                        continue
                    matching_completed_pending_invoices.append(inv)
            
            if not matching_completed_pending_invoices:
                continue
                
            matching_count = len(matching_completed_pending_invoices)
            total_price_inc_gst = round(o.get("total_price", 0.0) * 1.18)
            
            # Invoice values:
            order_invoice_count = matching_count
            order_invoice_amount = 0.0
            order_pending_amount = 0.0
            
            for inv in matching_completed_pending_invoices:
                # split values
                invoice_total_value = total_price_inc_gst / matching_count if matching_count > 0 else 0.0
                split_expected_amount = total_price_inc_gst / total_invoices_count if total_invoices_count > 0 else 0.0
                invoice_pending_value = max(split_expected_amount - float(inv.get("paid_amount") or 0), 0.0)
                
                order_invoice_amount += invoice_total_value
                order_pending_amount += invoice_pending_value
                
            if owner not in cart_owner_aggs:
                cart_owner_aggs[owner] = {
                    "total_invoice_count": 0,
                    "total_invoice_amount": 0.0,
                    "total_pending_amount": 0.0
                }
            cart_owner_aggs[owner]["total_invoice_count"] += order_invoice_count
            cart_owner_aggs[owner]["total_invoice_amount"] += order_invoice_amount
            cart_owner_aggs[owner]["total_pending_amount"] += order_pending_amount
            
            # Add to owners_data list
            owners_data.append({
                "owner_name": owner,
                "customer_name": o.get("customer_name") or "",
                "order_id": o.get("ui_id") or "",
                "invoice_count": order_invoice_count,
                "invoice_amount": round(order_invoice_amount, 2),
                "pending_amount": round(order_pending_amount, 2),
            })

        # Update owner_summaries
        owner_sum_dict = {s["owner_name"]: s for s in owner_summaries}
        for owner, cart_vals in cart_owner_aggs.items():
            if owner in owner_sum_dict:
                owner_sum_dict[owner]["total_invoice_count"] += cart_vals["total_invoice_count"]
                owner_sum_dict[owner]["total_invoice_amount"] = round(owner_sum_dict[owner]["total_invoice_amount"] + cart_vals["total_invoice_amount"], 2)
                owner_sum_dict[owner]["total_pending_amount"] = round(owner_sum_dict[owner]["total_pending_amount"] + cart_vals["total_pending_amount"], 2)
            else:
                owner_sum_dict[owner] = {
                    "owner_name": owner,
                    "total_invoice_count": cart_vals["total_invoice_count"],
                    "total_invoice_amount": round(cart_vals["total_invoice_amount"], 2),
                    "total_pending_amount": round(cart_vals["total_pending_amount"], 2),
                }
        owner_summaries = sorted(list(owner_sum_dict.values()), key=lambda x: x["owner_name"])

        # Update grand_total
        grand_total["invoice_count"] += sum(v["total_invoice_count"] for v in cart_owner_aggs.values())
        grand_total["invoice_amount"] = round(grand_total["invoice_amount"] + sum(v["total_invoice_amount"] for v in cart_owner_aggs.values()), 2)
        grand_total["pending_amount"] = round(grand_total["pending_amount"] + sum(v["total_pending_amount"] for v in cart_owner_aggs.values()), 2)

        # Sort owners_data by owner_name, customer_name, and order_id
        owners_data = sorted(owners_data, key=lambda x: (x["owner_name"], x["customer_name"], x["order_id"]))

        return {
            "owners": owners_data,
            "owner_summaries": owner_summaries,
            "grand_total": grand_total
        }

    async def get_distributor_projection_report(self, distributor_id, from_date, to_date, starting_month=None, date_by=OrderFilterDateByEnum.ACTIVATION_DATE.value):
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
        ]

        if distributor_id and distributor_id.upper() != 'ALL':
            conditions.append(Orders.distributor_id == distributor_id)

        if from_date:
            conditions.append(date_field >= from_date)
        if to_date:
            conditions.append(date_field <= to_date)

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

        # --- Group and combine standard Orders and Cart Orders ---
        from datetime import date, datetime
        monthly_totals = {}
        
        # 1. Add standard rows
        for row in rows:
            month_str = row["order_month"]
            month_sort = row["order_month_sort"]
            if hasattr(month_sort, 'date'):
                month_sort = month_sort.date()
            if isinstance(month_sort, str):
                month_sort = datetime.strptime(month_sort[:10], "%Y-%m-%d").date()
                
            monthly_totals[month_sort] = {
                "order_month": month_str,
                "order_month_sort": month_sort,
                "total_value": float(row["total_value"] or 0)
            }

        # 2. Retrieve and group Cart Orders
        cart_mapped_orders = await self._get_filtered_cart_orders(
            from_date=from_date,
            to_date=to_date,
            owner_name=None,
            date_by=date_by,
            distributor_id=distributor_id
        )

        date_by_val = date_by.value if hasattr(date_by, 'value') else date_by

        for o in cart_mapped_orders:
            o_date = None
            if date_by_val == OrderFilterDateByEnum.ACTIVATION_DATE.value:
                o_date = o.get("delivery_info", {}).get("delivery_date")
            elif date_by_val == OrderFilterDateByEnum.REQUESTED_DATE.value:
                o_date = o.get("delivery_info", {}).get("requested_date")
            else:
                o_date = o.get("created_at")

            parsed_date = None
            if o_date:
                if isinstance(o_date, (datetime, date)):
                    parsed_date = o_date if isinstance(o_date, date) else o_date.date()
                else:
                    try:
                        parsed_date = datetime.strptime(str(o_date)[:10], "%Y-%m-%d").date()
                    except Exception:
                        pass
            if not parsed_date:
                parsed_date = date.today()
                
            month_sort = date(parsed_date.year, parsed_date.month, 1)
            month_str = month_sort.strftime("%b-%y")
            
            dist_val = float(o.get("distributor_price") or 0.0)
            
            if month_sort not in monthly_totals:
                monthly_totals[month_sort] = {
                    "order_month": month_str,
                    "order_month_sort": month_sort,
                    "total_value": 0.0
                }
            monthly_totals[month_sort]["total_value"] += dist_val

        sorted_monthly_list = sorted(monthly_totals.values(), key=lambda x: x["order_month_sort"], reverse=True)

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

        for row in sorted_monthly_list:
            order_month_str = row["order_month"]
            total_value = float(row["total_value"] or 0)
            split_value = round(total_value / 12, 2) if total_value else 0
            
            # Base month object (the actual month of the order)
            base_date = row["order_month_sort"]
            if isinstance(base_date, datetime):
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

    async def get_pending_invoice_alert(self, days_threshold: int):
        activation_date = cast(Orders.delivery_info['delivery_date'].astext, Date)
        stmt = (
            select(
                Orders.id.label("order_id"),
                Orders.ui_id.label("ui_id"),
                Customers.name.label("customer_name"),
                Customers.owner.label("owner_name"),
                activation_date.label("created_at"),
                (func.current_date() - activation_date).label("days_since_created"),
                func.min(OrdersPaymentInvoiceInfo.invoice_status).label("invoice_status"),
                func.count(OrdersPaymentInvoiceInfo.id).label("pending_invoice_count")
            )
            .join(Customers, Orders.customer_id == Customers.id)
            .join(OrdersPaymentInvoiceInfo, Orders.id == OrdersPaymentInvoiceInfo.order_id)
            .where(
                and_(
                    OrdersPaymentInvoiceInfo.invoice_status == InvoiceStatus.INCOMPLETED.value,
                    Orders.is_deleted == False,
                    activation_date <= (func.current_date() - days_threshold) if days_threshold > 0 else True
                )
            )
            .group_by(
                Orders.id,
                Orders.ui_id,
                Customers.name,
                Customers.owner,
                activation_date
            )
            .order_by(desc(activation_date))
        )
        
        results = (await self.session.execute(stmt)).mappings().all()
        
        # --- Retrieve and process Cart Orders ---
        cart_mapped_orders = await self._get_filtered_cart_orders(
            from_date=None,
            to_date=None,
            owner_name=None,
            date_by=None
        )

        from datetime import date, datetime
        today = date.today()
        cart_alerts = []

        for o in cart_mapped_orders:
            o_del_date_str = o.get("delivery_info", {}).get("delivery_date")
            o_del_date = None
            if o_del_date_str:
                if isinstance(o_del_date_str, (datetime, date)):
                    o_del_date = o_del_date_str if isinstance(o_del_date_str, date) else o_del_date_str.date()
                else:
                    try:
                        o_del_date = datetime.strptime(str(o_del_date_str)[:10], "%Y-%m-%d").date()
                    except Exception:
                        pass
            
            if not o_del_date:
                continue
                
            days_since = (today - o_del_date).days
            if days_threshold > 0 and days_since < days_threshold:
                continue
                
            invoices = o.get("status_info") or []
            pending_invoice_count = sum(1 for inv in invoices if inv.get("invoice_status") == "INCOMPLETED")
            
            if pending_invoice_count > 0:
                cart_alerts.append({
                    "order_id": o.get("id"),
                    "ui_id": o.get("ui_id"),
                    "customer_name": o.get("customer_name") or "",
                    "owner_name": o.get("owner_name") or "Others",
                    "created_at": o_del_date,
                    "days_since_created": days_since,
                    "invoice_status": "INCOMPLETED",
                    "pending_invoice_count": pending_invoice_count
                })

        # --- Merge and Sort ---
        final_results = []
        for r in results:
            r_dict = dict(r)
            c_at = r_dict.get("created_at")
            if c_at and not isinstance(c_at, date):
                if isinstance(c_at, datetime):
                    r_dict["created_at"] = c_at.date()
                else:
                    try:
                        r_dict["created_at"] = datetime.strptime(str(c_at)[:10], "%Y-%m-%d").date()
                    except Exception:
                        pass
            final_results.append(r_dict)
            
        final_results.extend(cart_alerts)
        final_results = sorted(
            final_results,
            key=lambda x: x["created_at"] if x["created_at"] is not None else date.min,
            reverse=True
        )

        return final_results

    async def get_activation_date_alert(self, days_before: Optional[int] = 2, days_after: Optional[int] = 2):
        async def _get_alert_data(start_date_expr, end_date_expr):
            diff_col = (cast(Orders.delivery_info['delivery_date'].astext, Date) - func.current_date()).label("days_diff")
            
            stmt = (
                select(
                    Orders.id.label("order_id"),
                    Orders.ui_id.label("ui_id"),
                    Customers.name.label("customer_name"),
                    Customers.owner.label("owner_name"),
                    Orders.delivery_info['delivery_date'].astext.label("activation_date"),
                    diff_col
                )
                .join(Customers, Orders.customer_id == Customers.id)
                .where(
                    and_(
                        Orders.activated == False,
                        Orders.is_deleted == False,
                        cast(Orders.delivery_info['delivery_date'].astext, Date) >= start_date_expr if start_date_expr is not None else True,
                        cast(Orders.delivery_info['delivery_date'].astext, Date) <= end_date_expr if end_date_expr is not None else True
                    )
                )
                .order_by(cast(Orders.delivery_info['delivery_date'].astext, Date))
            )
            res = await self.session.execute(stmt)
            return [dict(r) for r in res.mappings().all()]

        # Upcoming: From today onwards (limited by days_before if > 0)
        upcoming = await _get_alert_data(
            func.current_date(), 
            (func.current_date() + days_before) if days_before > 0 else None
        )
        
        # Overdue: Everything in the past up to (today - days_after)
        overdue = await _get_alert_data(
            None, 
            (func.current_date() - max(1, days_after))
        )

        # --- Retrieve and process Cart Orders ---
        cart_mapped_orders = await self._get_filtered_cart_orders(
            from_date=None,
            to_date=None,
            owner_name=None,
            date_by=None
        )

        from datetime import date, datetime, timedelta
        today = date.today()
        
        cart_upcoming = []
        cart_overdue = []
        
        for o in cart_mapped_orders:
            if o.get("activated") == True:
                continue
                
            o_del_date_str = o.get("delivery_info", {}).get("delivery_date")
            o_del_date = None
            if o_del_date_str:
                if isinstance(o_del_date_str, (datetime, date)):
                    o_del_date = o_del_date_str if isinstance(o_del_date_str, date) else o_del_date_str.date()
                else:
                    try:
                        o_del_date = datetime.strptime(str(o_del_date_str)[:10], "%Y-%m-%d").date()
                    except Exception:
                        pass
            
            if not o_del_date:
                continue
                
            days_diff = (o_del_date - today).days
            
            cart_alert = {
                "order_id": o.get("id"),
                "ui_id": o.get("ui_id"),
                "customer_name": o.get("customer_name") or "",
                "owner_name": o.get("owner_name") or "Others",
                "activation_date": o_del_date.strftime("%Y-%m-%d"),
                "days_diff": days_diff
            }
            
            # Categorize
            # Upcoming
            is_upcoming = o_del_date >= today
            if days_before is not None and days_before > 0:
                is_upcoming = is_upcoming and (o_del_date <= today + timedelta(days=days_before))
            if is_upcoming:
                cart_upcoming.append(cart_alert)
                
            # Overdue
            is_overdue = o_del_date <= today - timedelta(days=max(1, days_after if days_after is not None else 2))
            if is_overdue:
                cart_overdue.append(cart_alert)

        # --- Merge and Sort Chronologically ---
        combined_upcoming = [dict(u) for u in upcoming] + cart_upcoming
        combined_upcoming = sorted(combined_upcoming, key=lambda x: x["activation_date"])

        combined_overdue = [dict(o_d) for o_d in overdue] + cart_overdue
        combined_overdue = sorted(combined_overdue, key=lambda x: x["activation_date"])

        return {"upcoming": combined_upcoming, "overdue": combined_overdue}






    async def get_owner_sales_report(self, from_date, to_date, date_by, cur_user_id, user_role):
        date_by_val = date_by.value if hasattr(date_by, 'value') else date_by
        
        if date_by_val == "ACTIVATION_DATE":
            date_field = cast(Orders.delivery_info["delivery_date"].astext, Date)
        elif date_by_val == "REQUESTED_DATE":
            date_field = cast(Orders.delivery_info["requested_date"].astext, Date)
        else:
            date_field = func.date(func.timezone("Asia/Kolkata", Orders.created_at))

        conditions = [Orders.is_deleted == False]
        if from_date:
            conditions.append(date_field >= from_date)
        if to_date:
            conditions.append(date_field <= to_date)
        
        # Removed owner_id check since Orders does not have owner_id
        
        owner_label = func.coalesce(Customers.owner, "Unknown").label("owner_name")
        product_type = Products.product_type.label("product_type")
        
        stmt = (
            select(
                owner_label,
                customer_final_price.label("customer_price"),
                Orders.logistic_info["purchase_type"].astext.label("purchase_type"),
                product_type
            )
            .select_from(Orders)
            .join(Customers, Customers.id == Orders.customer_id, isouter=True)
            .join(Products, Products.id == Orders.product_id, isouter=True)
            .where(*conditions)
        )
        
        result = await self.session.execute(stmt)
        rows = result.all()
        
        owner_map = {}
        for row in rows:
            o_name = row.owner_name
            c_price = float(row.customer_price or 0)
            val = c_price
            p_type = row.product_type
            purchase_type = row.purchase_type
            
            if o_name not in owner_map:
                owner_map[o_name] = {
                    "owner_name": o_name,
                    "total_order_value": 0,
                    "net_new_customer_value": 0,
                    "product_types": {}
                }
            
            owner_map[o_name]["total_order_value"] += val
            
            if purchase_type == "NET-NEW-CUSTOMER":
                owner_map[o_name]["net_new_customer_value"] += val
                
            if p_type:
                if p_type not in owner_map[o_name]["product_types"]:
                    owner_map[o_name]["product_types"][p_type] = 0
                owner_map[o_name]["product_types"][p_type] += val
                
        return {"owners": list(owner_map.values())}



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

class PendingInvoiceReportRepo(OrdersRepo):
    async def get(self, **kwargs):
        cursor = kwargs.get('cursor', 1)
        if cursor is not None and int(cursor) != 1:
            return {"data": [], "next_cursor": None}
            
        # Extract parameters - handle string values from background jobs
        days_threshold = kwargs.get('days_threshold')
        if isinstance(days_threshold, str):
            days_threshold = int(days_threshold)
        elif days_threshold is None:
            days_threshold = 0
            
        data = await self.get_pending_invoice_alert(days_threshold=days_threshold)
        
        return {
            "data": data,
            "next_cursor": None
        }

class ActivationAlertReportRepo(OrdersRepo):
    async def get(self, **kwargs):
        cursor = kwargs.get('cursor', 1)
        if cursor is not None and int(cursor) != 1:
            return {"data": [], "next_cursor": None}
            
        days_before = kwargs.get('days_before', 2)
        days_after = kwargs.get('days_after', 2)
        
        if isinstance(days_before, str): days_before = int(days_before)
        if isinstance(days_after, str): days_after = int(days_after)
            
        report = await self.get_activation_date_alert(
            days_before=days_before,
            days_after=days_after
        )
        
        upcoming = [{**r, "status": "Upcoming"} for r in report["upcoming"]]
        overdue = [{**r, "status": "Overdue"} for r in report["overdue"]]
        
        return {
            "data": upcoming + overdue,
            "next_cursor": None
        }




