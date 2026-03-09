from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from infras.primary_db.models.order import Orders,OrdersPaymentInvoiceInfo
from infras.primary_db.models.user import Users
from infras.primary_db.services.order_service import OrdersService,OrdersRepo
from infras.primary_db.models.product import Products
from infras.primary_db.models.distributor import Distributors
from infras.primary_db.models.customer import Customers
from datetime import datetime,date
from sqlalchemy import select,func,case,cast,Numeric,Date,and_
from typing import Optional
from icecream import ic
from core.data_formats.enums.user_enums import UserRoles
from core.data_formats.enums.order_enums import PaymentStatus,InvoiceStatus
from schemas.request_schemas.order import OrderFilterSchema,OrderDateFilterTypDict
from core.data_formats.enums.order_enums import OrderFilterDateByEnum
from core.utils.calculations import get_customer_addon_price,get_customer_price,get_distri_addon_price,get_distributor_price,get_profit_loss_price,get_remaining_days,get_total_price
from infras.primary_db.calculations import distri_final_price,customer_final_price,profit_loss_price

class HandleDashboardRequest:
    def __init__(self,session:AsyncSession,user_role:UserRoles,cur_user_id:str):
        self.session=session
        self.user_role=user_role,
        self.cur_user_id=cur_user_id

    async def get_dashboard(self,from_date:Optional[date]=None,to_date:Optional[date]=None,timezone: Optional[str]="Asia/Kolkata"):
        # day_expr = func.date(func.timezone(timezone, Orders.delivery_info['requested_date']))
        day_expr = cast(
            Orders.delivery_info["delivery_date"].astext,
            Date    
        ).label("day")
        
        payment_subq = (
            select(
                OrdersPaymentInvoiceInfo.order_id,

                # detect pending invoice per order
                func.bool_or(
                    OrdersPaymentInvoiceInfo.invoice_status == InvoiceStatus.INCOMPLETED.value
                ).label("has_pending_invoice"),

                # detect pending payment per order
                func.bool_or(
                    and_(
                        OrdersPaymentInvoiceInfo.payment_status != PaymentStatus.PAID.value,
                        OrdersPaymentInvoiceInfo.payment_status != PaymentStatus.FULL_PAYMENT_RECEIVED.value
                    )
                ).label("has_pending_due")
            )
            .group_by(OrdersPaymentInvoiceInfo.order_id)
            .subquery()
        )


        stmt = (
            select(

                func.count(Orders.id).label("total_orders"),
                day_expr.label("day"),
                func.count().filter(
                    payment_subq.c.has_pending_due
                ).label("pending_dues"),

                func.count().filter(
                    payment_subq.c.has_pending_invoice
                ).label("pending_invoices"),

                func.round(
                    func.coalesce(func.sum(profit_loss_price), 0)
                ).label("total_revenue"),

                func.round(
                    func.coalesce(func.sum(customer_final_price), 0)
                ).label("order_value"),
            )

            .select_from(Orders)

            .join(payment_subq, payment_subq.c.order_id == Orders.id, isouter=True)

            .join(Products, Products.id == Orders.product_id, isouter=True)
            .join(Customers, Customers.id == Orders.customer_id, isouter=True)
            .join(Distributors, Distributors.id == Orders.distributor_id, isouter=True)
            .join(Users, Users.id == Orders.deleted_by, isouter=True)
            .where(Orders.is_deleted == False)
            .group_by(day_expr)
        )


        if from_date and to_date:
            stmt=stmt.where(and_(day_expr>=from_date),day_expr<=to_date)
    
        result = await self.session.execute(stmt)

        dashboard = result.mappings().all()

        return {
            "dashboard_datas": dashboard
        }
    

    async def get_distri_dashboard(self,from_date:Optional[date]=None,to_date:Optional[date]=None,timezone: Optional[str]="Asia/Kolkata"):
        distri_ids=(await self.session.execute(select(Distributors.id))).scalars().all()
        filter=OrderFilterSchema()
        if from_date and to_date:
            filter=OrderFilterSchema(date_filter=OrderDateFilterTypDict(from_date=from_date,to_date=to_date,by=OrderFilterDateByEnum.ACTIVATION_DATE))
        distri_dashboard=[]
        for id in distri_ids:
            order_infos=await OrdersService(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).get(filter=filter,limit=1,query=id)
            ic(order_infos)
            if len(order_infos['orders'])>0:
                order_infos['name']=order_infos['orders'][0]['distributor_name'] 
                order_infos['ui_id']=order_infos['orders'][0]['distributor_ui_id']
                del order_infos['next_cursor']
                del order_infos['orders']
                distri_dashboard.append(order_infos)
        
        return {'distributor_datas':distri_dashboard}