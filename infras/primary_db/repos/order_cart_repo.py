from typing import cast,List
from . import HTTPException,BaseRepoModel
from ..models.order import CartOrders,OrdersPaymentInvoiceInfo,CartOrdersProduct,CartOrdersPaymentInvoiceInfo,CartOrdersAdditionalQuantity
from ..models.product import Products
from ..models.customer import Customers
from ..models.distributor import Distributors
from core.utils.uuid_generator import generate_uuid
from sqlalchemy import Numeric, select,delete,update,or_,func,String,cast,case,and_,Date,desc,text,exists
from sqlalchemy.orm import aliased
from sqlalchemy.ext.asyncio import AsyncSession
from icecream import ic
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import literal,true
from core.data_formats.enums.user_enums import UserRoles
from core.data_formats.enums.order_enums import PaymentStatus,InvoiceStatus,PurchaseTypes,OrderFilterRevenueEnum,ActivationStatusEnum
from schemas.db_schemas.order import AddCartOrderDbSchema,UpdateCartOrderProductDbSchema,UpdateCartOrderDbSchema,AddCartOrderProductDbSchema,UpdateCartOrderQuantityDbSchema
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

CartQty = aliased(CartOrdersAdditionalQuantity)

class OrdersCartRepo(BaseRepoModel):
    def __init__(self,session:AsyncSession,user_role:UserRoles,cur_user_id:str):
        self.session=session
        self.user_role=user_role
        self.cur_user_id=cur_user_id
        self.product_subquery=(
            select(
                CartOrdersProduct.order_id,
                
                func.json_agg(
                    func.json_build_object(
                        "id",CartOrdersProduct.id,
                        "product_id", CartOrdersProduct.product_id,
                        "additional_discount", CartOrdersProduct.additional_discount,
                        "additional_price", CartOrdersProduct.additional_price,
                        "unit_price", CartOrdersProduct.unit_price,
                        "discount_id", CartOrdersProduct.discount_id,
                        "discount" , Distributors.discounts[CartOrdersProduct.discount_id],
                        "vendor_commision", CartOrdersProduct.vendor_commision,
                        "quantity", CartOrdersProduct.quantity,
                        "name", Products.name,
                        "add_on_quantity",CartOrdersAdditionalQuantity.quantity,
                        "price", Products.price,
                    )
                ).label("products")
            )
            .join(
                CartOrdersAdditionalQuantity,
                CartOrdersAdditionalQuantity.cart_product_id == CartOrdersProduct.id,
                isouter=True
            )
            .join(CartOrders, CartOrders.id == CartOrdersProduct.order_id)
            .join(Distributors,Distributors.id==CartOrders.distributor_id)
            .join(Products, Products.id == CartOrdersProduct.product_id)
            .group_by(CartOrdersProduct.order_id)  # Only group in the subquery
        ).subquery()

        self.payment_subquery = (
            select(
                CartOrdersPaymentInvoiceInfo.order_id,
                func.coalesce(
                    func.jsonb_agg(
                        func.jsonb_build_object(
                            "invoice_number", CartOrdersPaymentInvoiceInfo.invoice_number,
                            "invoice_date", CartOrdersPaymentInvoiceInfo.invoice_date,
                            "invoice_status", CartOrdersPaymentInvoiceInfo.invoice_status,
                            "payment_status", CartOrdersPaymentInvoiceInfo.payment_status,
                            "paid_amount", CartOrdersPaymentInvoiceInfo.paid_amount
                        )
                    ).filter(CartOrdersPaymentInvoiceInfo.id.isnot(None)),
                    func.cast("[]", JSONB)
                ).label("status_info"),
                func.coalesce(
                    func.sum(CartOrdersPaymentInvoiceInfo.paid_amount), 0
                ).label("total_paid_amount"),
            )
            .group_by(CartOrdersPaymentInvoiceInfo.order_id)
            .subquery()
        )

        self.orders_cols=(
            CartOrders.id,
            CartOrders.ui_id,
            CartOrders.sequence_id,
            CartOrders.customer_id,
            CartOrders.logistic_info,
            CartOrders.delivery_info,
            CartOrders.activated,
            CartOrders.created_at,
            Customers.name.label("customer_name"),
            Customers.email.label("customer_email"),
            Customers.mobile_number,
            CartOrders.distributor_id,
            Distributors.name.label("distributor_name"),
            self.product_subquery.c.products,
            func.coalesce(self.payment_subquery.c.status_info, func.cast("[]", JSONB)).label("status_info"),
            func.coalesce(self.payment_subquery.c.total_paid_amount, 0).label("total_paid_amount")
        )


    @start_db_transaction
    async def add(self,order_data:AddCartOrderDbSchema,product_datas:List[CartOrdersProduct]):
        self.session.add(CartOrders(**order_data.model_dump(mode='json',exclude=['lui_id','status_info','products'])))
        self.session.add_all(product_datas)
        invoicetoadd=order_data.model_dump(mode='json')

        invoicetoadd_bulk=[]
        for status in invoicetoadd['status_info']:
            if status.get("payment_status") in ("FULL PAYMENT RECEIVED", "PAID"):
                status["paid_amount"] = status.get("paid_amount") if status.get("paid_amount") is not None else (status.get("invoice_amount") or 0.0)
                status["remaining_amount"] = 0.0
            clean_status = {
                k: v for k, v in status.items()
                if k in ("id", "payment_status", "invoice_status", "invoice_number", "invoice_date", "paid_amount")
            }
            invoicetoadd_bulk.append(CartOrdersPaymentInvoiceInfo(**clean_status,order_id=order_data.id))
        
        self.session.add_all(invoicetoadd_bulk)
        await self.session.execute(update(TablesUiLId).where(TablesUiLId.id=="1").values(cart_order_luiid=order_data.ui_id))
        # need to implement invoice generation process + email sending
        return True

    
    @start_db_transaction
    async def update(self,order_data:UpdateCartOrderDbSchema,products_data:List[dict]):
        data_toupdate=order_data.model_dump(mode='json',exclude=['product_id','customer_id','order_id','status_info','products'],exclude_none=True,exclude_unset=True)
        if not data_toupdate or len(data_toupdate)<1:
            return ErrorResponseTypDict(status_code=400,success=False,msg="Error : Updating Order",description="No valid fields to update provided")
        
        invoicetoadd=order_data.model_dump(mode='json')
        invoicetoadd_bulk=[]
        await self.session.execute(delete(CartOrdersPaymentInvoiceInfo).where(CartOrdersPaymentInvoiceInfo.order_id==order_data.order_id))
        for status in invoicetoadd['status_info']:
            if status.get("payment_status") in ("FULL PAYMENT RECEIVED", "PAID"):
                status["paid_amount"] = status.get("paid_amount") if status.get("paid_amount") is not None else (status.get("invoice_amount") or 0.0)
                status["remaining_amount"] = 0.0
            clean_status = {
                k: v for k, v in status.items()
                if k in ("id", "payment_status", "invoice_status", "invoice_number", "invoice_date", "paid_amount")
            }
            invoicetoadd_bulk.append(CartOrdersPaymentInvoiceInfo(**clean_status,order_id=order_data.order_id))
        self.session.add_all(invoicetoadd_bulk)


        await self.session.run_sync(
            lambda s: s.bulk_update_mappings(CartOrdersProduct,products_data)
        )


        cart_order_toupdate=update(CartOrders).where(CartOrders.id==order_data.order_id).values(
            **data_toupdate
        ).returning(CartOrders.id)

        is_updated=(await self.session.execute(cart_order_toupdate)).scalar_one_or_none()
        
        # need to implement invoice generation process + email sending
        return is_updated if is_updated else ErrorResponseTypDict(status_code=400,success=False,msg="Error : Updating Order",description="Unable to update the order, may be invalid order id or no changes in data")

    @start_db_transaction    
    async def delete(self,order_id:str,soft_delete:bool=True):
        ic(soft_delete)
        if soft_delete:
            cart_order_todelete=update(CartOrders).where(CartOrders.id==order_id,CartOrders.is_deleted==False).values(
                is_deleted=True,
                deleted_at=func.now(),
                deleted_by=self.cur_user_id
            ).returning(CartOrders.id)

            is_deleted=(await self.session.execute(cart_order_todelete)).scalar_one_or_none()

        else:
            if self.user_role if isinstance(self.user_role,UserRoles) else self.user_role!=UserRoles.SUPER_ADMIN.value:
                return ErrorResponseTypDict(status_code=403,success=False,msg="Error : Deleting Order",description="Only super admin can perform hard delete operation")
            
            cart_order_todelete=delete(CartOrders).where(CartOrders.id==order_id).returning(CartOrders.id)
            is_deleted=(await self.session.execute(cart_order_todelete)).scalar_one_or_none()
            
            # need to implement email sending "Your orders has been stoped from CRM"
        return is_deleted if is_deleted else ErrorResponseTypDict(status_code=400,success=False,msg="Error : Deleting Order",description="Unable to delete the order, may be invalid order id or order already deleted")
    

    async def get_by_id(self,order_id:str):
        stmt=(
            select(
                *self.orders_cols
            )
            .where(
                CartOrders.id==order_id,
                CartOrders.is_deleted==False
            )
            .join(Distributors,Distributors.id==CartOrders.distributor_id,isouter=True)
            .join(Customers, Customers.id == CartOrders.customer_id, isouter=True)
            .join(self.product_subquery, self.product_subquery.c.order_id == CartOrders.id, isouter=True)
            .join(self.payment_subquery, self.payment_subquery.c.order_id == CartOrders.id, isouter=True)
        )

        results=(await self.session.execute(stmt)).mappings().one_or_none()
        ic(results)
        if results:
            return self._map_single_cart_order(results)

        # Fallback to standard Orders if not found in CartOrders
        from ..models.order import Orders
        from infras.primary_db.repos.order_repo import OrdersRepo
        
        normal_repo = OrdersRepo(session=self.session, user_role=self.user_role, cur_user_id=self.cur_user_id)
        normal_stmt = (
            select(
                *normal_repo.orders_cols
            )
            .where(
                Orders.id == order_id,
                Orders.is_deleted == False
            )
            .join(Distributors, Distributors.id == Orders.distributor_id, isouter=True)
            .join(Customers, Customers.id == Orders.customer_id, isouter=True)
            .join(Products, Products.id == Orders.product_id, isouter=True)
            .join(normal_repo.subquery, normal_repo.subquery.c.order_id == Orders.id, isouter=True)
        )
        
        normal_row = (await self.session.execute(normal_stmt)).mappings().one_or_none()
        if normal_row:
            o = dict(normal_row)
            products_list = [{
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
            return {
                "id": o.get("id"),
                "ui_id": o.get("ui_id"),
                "customer_id": o.get("customer_id"),
                "customer_name": o.get("customer_name"),
                "customer_email": o.get("customer_email") or "",
                "distributor_id": o.get("distributor_id"),
                "distributor_name": o.get("distributor_name"),
                "products": products_list,
                "status_info": o.get("status_info") or [],
                "delivery_info": o.get("delivery_info") or {},
                "logistic_info": o.get("logistic_info") or {},
                "activated": o.get("activated"),
                "created_at": o.get("created_at"),
            }
        return results


    @start_db_transaction
    async def update_qty(self,data:UpdateCartOrderQuantityDbSchema):
        datas_toadd=[]
        for product in data.products:
            datas_toadd.append(
                CartOrdersAdditionalQuantity(
                    quantity=product['quantity'],
                    type=data.type,
                    cart_order_id=data.order_id,
                    cart_product_id=product['product_id']
                )
            )
        self.session.add_all(datas_toadd)

        return True


        
    async def get(
        self,
        filter: Optional[OrderFilterSchema]=OrderFilterSchema(),
        cursor: int = 1,
        limit: int = 10,
        query: str = '',
        include_deleted: bool = False,
        in_search:List=[]
    ):
        cursor = int(cursor)
        limit = int(limit)
        
        # 1. Fetch all matching active records to compute accurate global stats
        stmt_all = (
            select(
                *self.orders_cols
            )
            .where(
                CartOrders.is_deleted==False
            )
            .join(Distributors,Distributors.id==CartOrders.distributor_id,isouter=True)
            .join(Customers, Customers.id == CartOrders.customer_id, isouter=True)
            .join(self.product_subquery, self.product_subquery.c.order_id == CartOrders.id, isouter=True)
            .join(self.payment_subquery, self.payment_subquery.c.order_id == CartOrders.id, isouter=True)
            .order_by(desc(CartOrders.created_at))
        )

        all_results = (await self.session.execute(stmt_all)).mappings().all()

        # 2. Map all records using our python helper
        all_mapped = [self._map_single_cart_order(row) for row in all_results]

        # 3. Calculate statistics
        total_revenue = 0.0
        distributor_value = 0.0
        total_license = 0
        total_orders = len(all_mapped)
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

        for o in all_mapped:
            order_total_price = o.get("total_price") or 0.0
            order_distributor_price = o.get("distributor_price") or 0.0
            order_vendor_total_price = o.get("vendor_total_price") or 0.0
            order_profit_loss = o.get("profit_loss") or 0.0
            order_license = o.get("total_license") or 0
            purchase_type = o.get("logistic_info", {}).get("purchase_type") or ""
            
            total_revenue += order_profit_loss
            distributor_value += order_distributor_price
            total_license += order_license
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
                    remaining_bal = 0
                
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
                elif invoice_status == "PENDING":
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

        # 4. Paginate
        start_idx = 0 if cursor == 1 else cursor
        end_idx = start_idx + limit
        paginated_orders = all_mapped[start_idx:end_idx]

        return {
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
            "purchase_stats": purchase_stats,
            "total_pages": ceil(total_orders / limit) if limit > 0 else 1,
            "next_cursor": paginated_orders[-1]["sequence_id"] if (len(paginated_orders) > 0 and paginated_orders[-1].get("sequence_id") != 1) else None,
            "orders": paginated_orders
        }
    
    async def search(self,query:str):
        ...

    def _parse_date(self, d_str):
        from datetime import date
        if not d_str:
            return None
        if isinstance(d_str, (datetime, date)):
            return d_str
        try:
            return datetime.strptime(d_str, "%Y-%m-%d").date()
        except Exception:
            try:
                return datetime.fromisoformat(d_str.replace("Z", "+00:00")).date()
            except Exception:
                return None

    def _calculate_remaining_days(self, logistic_info, delivery_info):
        last_expiry_str = logistic_info.get("last_ord_expiry_date")
        delivery_date_str = delivery_info.get("delivery_date")
        if not last_expiry_str or not delivery_date_str:
            return 0
        
        last_expiry = self._parse_date(last_expiry_str)
        delivery_date = self._parse_date(delivery_date_str)
        
        if not last_expiry or not delivery_date:
            return 0
        
        expiry_date = last_expiry + timedelta(days=366)
        rem_days = (expiry_date - delivery_date).days
        return max(rem_days, 0)

    def _calculate_product_prices(self, product, purchase_type, remaining_days):
        product_price = float(product.get("price") or 0)
        additional_price = float(product.get("additional_price") or 0)
        qty = float(product.get("quantity") or 0)
        
        unit_price = float(product.get("unit_price") or 0)
        customer_tot_price = round(unit_price * qty)
        
        if purchase_type == "EXISTING-ADD-ON":
            customer_final_price = round((customer_tot_price / 365) * remaining_days)
        else:
            customer_final_price = round(customer_tot_price)
            
        customer_final_price_inc_gst = round(customer_final_price * 1.18)
        
        distributor_tot_price = round((product_price + additional_price) * qty)
        
        dist_discount_str = "0"
        discount_obj = product.get("discount")
        if isinstance(discount_obj, dict):
            dist_discount_str = str(discount_obj.get("discount") or "0")
        else:
            dist_discount_str = str(product.get("distributor_discount") or "0")
            
        add_discount_str = str(product.get("additional_discount") or "0")
        
        def parse_disc_val(disc_str, tot_price):
            disc_str = disc_str.strip()
            if "%" in disc_str:
                pct = float(disc_str.replace("%", "").strip() or 0)
                return round(tot_price * (pct / 100))
            else:
                try:
                    return round(float(disc_str or 0))
                except Exception:
                    return 0
                    
        distri_disc_price = parse_disc_val(dist_discount_str, distributor_tot_price)
        distri_additi_price = parse_disc_val(add_discount_str, distributor_tot_price)
        
        if purchase_type == "EXISTING-ADD-ON":
            distri_final_price = round(((distributor_tot_price - (distri_additi_price + distri_disc_price)) / 365) * remaining_days)
        else:
            distri_final_price = round(distributor_tot_price - (distri_additi_price + distri_disc_price))
            
        vendor_commision = str(product.get("vendor_commision") or "0")
        if "%" in vendor_commision:
            pct = float(vendor_commision.replace("%", "").strip() or 0)
            vendor_disc_price = round(unit_price * (pct / 100) * qty)
        else:
            try:
                vendor_disc_price = round(float(vendor_commision or 0) * qty)
            except Exception:
                vendor_disc_price = 0
                
        profit_loss = round(customer_final_price - vendor_disc_price - distri_final_price)
        
        return {
            "customer_price": float(customer_final_price),
            "customer_price_inc_gst": float(customer_final_price_inc_gst),
            "distributor_price": float(distri_final_price),
            "vendor_total_price": float(vendor_disc_price),
            "profit_loss": float(profit_loss),
            "quantity": int(qty),
            "unit_price": unit_price,
            "additional_price": additional_price,
            "additional_discount": add_discount_str,
            "vendor_commision": vendor_commision,
            "price": product_price
        }

    def _map_single_cart_order(self, row):
        from datetime import date
        o = dict(row)
        
        if o.get("created_at"):
            if isinstance(o["created_at"], (datetime, date)):
                o["order_created_at"] = o["created_at"].strftime("%Y-%m-%d")
            else:
                o["order_created_at"] = str(o["created_at"])[:10]
        else:
            o["order_created_at"] = None
            
        logistic_info = o.get("logistic_info") or {}
        delivery_info = o.get("delivery_info") or {}
        purchase_type = logistic_info.get("purchase_type") or ""
        
        rem_days = self._calculate_remaining_days(logistic_info, delivery_info)
        o["remaining_days"] = rem_days
        
        order_total_price = 0.0
        order_distributor_price = 0.0
        order_vendor_total_price = 0.0
        order_profit_loss = 0.0
        order_license = 0
        
        products_list = o.get("products") or []
        mapped_products = []
        for p in products_list:
            prices = self._calculate_product_prices(p, purchase_type, rem_days)
            order_total_price += prices["customer_price"]
            order_distributor_price += prices["distributor_price"]
            order_vendor_total_price += prices["vendor_total_price"]
            order_profit_loss += prices["profit_loss"]
            order_license += prices["quantity"]
            
            mapped_p = {
                **p,
                "customer_price": prices["customer_price"],
                "customer_price_inc_gst": prices["customer_price_inc_gst"],
                "distributor_price": prices["distributor_price"],
                "vendor_total_price": prices["vendor_total_price"],
                "profit_loss": prices["profit_loss"],
                "unit_price": prices["unit_price"],
                "additional_price": prices["additional_price"]
            }
            mapped_products.append(mapped_p)
            
        o["products"] = mapped_products
        o["total_price"] = order_total_price
        o["customer_price"] = order_total_price
        o["customer_total_price"] = order_total_price
        o["customer_amount_with_gst"] = round(order_total_price * 1.18)
        o["distributor_price"] = order_distributor_price
        o["distributor_total_price"] = order_distributor_price
        o["vendor_total_price"] = order_vendor_total_price
        o["vendor_commision"] = str(order_vendor_total_price)
        o["profit_loss"] = order_profit_loss
        o["total_license"] = order_license
        o["quantity"] = order_license
        
        o["customer_ui_id"] = f"CUST-T-2026-100000"
        o["distributor_ui_id"] = f"DIST-T-2026-100000"
        o["mobile_number"] = o.get("mobile_number") or ""
        
        return o

    




