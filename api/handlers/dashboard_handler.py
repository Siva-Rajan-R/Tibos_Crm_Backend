from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from infras.primary_db.models.order import Orders,PaymentStatus,InvoiceStatus
from datetime import datetime,date
from sqlalchemy import select,func,case,cast,Numeric,Date
from typing import Optional
from icecream import ic
from core.data_formats.enums.common_enums import UserRoles


class HandleDashboardRequest:
    def __init__(self,session:AsyncSession,user_role:UserRoles,cur_user_id:str):
        self.session=session
        self.user_role=user_role,
        self.cur_user_id=cur_user_id

    async def get_dashboard(self,from_date:Optional[date]=None,to_date:Optional[date]=None,timezone: Optional[str]="Asia/Kolkata"):
        # day_expr = func.date(func.timezone(timezone, Orders.delivery_info['requested_date']))
        day_expr = cast(
        Orders.delivery_info["requested_date"].astext,
        Date
    ).label("day")
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
            (vendor_comm_amount*cast(func.coalesce(Orders.quantity, 0), Numeric))
            -
            cast(func.coalesce(Orders.final_price, 0), Numeric)
        )
        stmt = select(
            day_expr.label("day"),
            func.count(Orders.id).label("total_orders"),
            func.count().filter(Orders.payment_status == PaymentStatus.NOT_PAID.value).label("pending_dues"),
            func.count().filter(Orders.invoice_status == InvoiceStatus.INCOMPLETED.value).label("pending_invoices"),
            func.round(func.coalesce(func.sum(profit_expr), 0)).label("total_revenue"),
            func.round(func.sum(Orders.unit_price*Orders.quantity)).label("order_value")
        ).where(
            Orders.is_deleted==False
        ).group_by(
            day_expr
        ).order_by(
            day_expr
        )

        if from_date and to_date:
            stmt=stmt.where(
                day_expr >= from_date,
                day_expr <= to_date
            )

        datas=(await self.session.execute(stmt)).mappings().all()
        ic(datas)
        return{'dashboard_datas':datas}