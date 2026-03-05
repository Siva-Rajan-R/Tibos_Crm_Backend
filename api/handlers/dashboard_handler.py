from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from infras.primary_db.models.order import Orders,OrdersPaymentInvoiceInfo
from infras.primary_db.services.order_service import OrdersService,OrdersRepo
from infras.primary_db.models.product import Products
from infras.primary_db.models.distributor import Distributors
from infras.primary_db.models.customer import Customers
from datetime import datetime,date
from sqlalchemy import select,func,case,cast,Numeric,Date
from typing import Optional
from icecream import ic
from core.data_formats.enums.user_enums import UserRoles
from core.data_formats.enums.order_enums import PaymentStatus,InvoiceStatus
from schemas.request_schemas.order import OrderFilterSchema,OrderDateFilterTypDict
from core.data_formats.enums.order_enums import OrderFilterDateByEnum
from core.utils.calculations import get_customer_addon_price,get_customer_price,get_distri_addon_price,get_distributor_price,get_profit_loss_price,get_remaining_days,get_total_price
from infras.primary_db.calculations import distri_final_price,customer_final_price,profit_loss_price


# vendor_comm_amount = case(
# (
#     Orders.vendor_commision.like('%\%%'),
#     # percentage: (unit_price * quantity) * percent / 100
#     (
#         cast(func.coalesce(Orders.unit_price, 0), Numeric) *
#         cast(func.coalesce(Orders.quantity, 0), Numeric)
#     )
#     *
#     (
#         cast(func.replace(Orders.vendor_commision, '%', ''), Numeric) / 100
#     )
# ),
# else_=cast(func.coalesce(Orders.vendor_commision, '0'), Numeric)
# )

# profit_expr = (
# (cast(func.coalesce(Orders.unit_price, 0), Numeric) *
# cast(func.coalesce(Orders.quantity, 0), Numeric))
# -
# (vendor_comm_amount*cast(func.coalesce(Orders.quantity, 0), Numeric))
# -
# cast(func.coalesce(get_distributor_price(product_price=Products.price,qty=Orders.quantity,distri_discount=Distributors.discount,addti_discount=Orders.additional_discount), 0), Numeric)
# )


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
        
        stmt = (
            select(
                day_expr,
                func.count(Orders.id).label("total_orders"),

                func.count().filter(
                    OrdersPaymentInvoiceInfo.payment_status == PaymentStatus.NOT_PAID.value
                ).label("pending_dues"),

                func.count().filter(
                    OrdersPaymentInvoiceInfo.invoice_status == InvoiceStatus.INCOMPLETED.value
                ).label("pending_invoices"),

                func.round(func.coalesce(func.sum(profit_loss_price), 0)).label("total_revenue"),
                func.round(func.sum(customer_final_price)).label("order_value")
            )
            .join(Products, Products.id == Orders.product_id, isouter=True)
            .join(Distributors, Distributors.id == Orders.distributor_id, isouter=True)
            .join(Customers, Customers.id == Orders.customer_id, isouter=True)

            # THIS JOIN IS REQUIRED
            .join(
                OrdersPaymentInvoiceInfo,
                OrdersPaymentInvoiceInfo.order_id == Orders.id,
                isouter=True
            )

            .where(Orders.is_deleted == False)
            .group_by(day_expr)
            .order_by(day_expr)
        )

        datas=(await self.session.execute(stmt)).mappings().all()
        ic(datas)
        return{'dashboard_datas':datas}
    

    async def get_distri_dashboard(self,from_date:Optional[date]=None,to_date:Optional[date]=None,timezone: Optional[str]="Asia/Kolkata"):
        distri_ids=(await self.session.execute(select(Distributors.id))).scalars().all()
        filter=OrderFilterSchema()
        if from_date and to_date:
            filter=OrderFilterSchema(date_filter=OrderDateFilterTypDict(from_date=from_date,to_date=to_date,by=OrderFilterDateByEnum.ACTIVATION_DATE))
        distri_dashboard=[]
        for id in distri_ids:
            order_infos=await OrdersService(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).get(filter=filter,limit=1,query=id)
            order_infos['name']=order_infos['orders'][0]['distributor_name']
            order_infos['ui_id']=order_infos['orders'][0]['distributor_ui_id']
            del order_infos['next_cursor']
            del order_infos['orders']
            distri_dashboard.append(order_infos)
        
        return {'distributor_datas':distri_dashboard}