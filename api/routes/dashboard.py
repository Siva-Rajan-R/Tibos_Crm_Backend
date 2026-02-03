from fastapi import Depends,APIRouter,Query
from infras.primary_db.main import get_pg_db_session,AsyncSession
from api.dependencies.token_verification import verify_user
from typing import Optional
from infras.primary_db.models.product import Products
from infras.primary_db.models.order import Orders,PaymentStatus,InvoiceStatus
from infras.primary_db.models.contact import Contacts
from infras.primary_db.models.customer import Customers
from infras.primary_db.models.user import Users
from datetime import datetime,date,timedelta
from sqlalchemy import select,func,case,cast,Numeric
from typing import Optional
from icecream import ic
import pytz

router=APIRouter(
    tags=['Dashboard'],
    prefix='/dashboard'
)


@router.get('/weeks')
async def get_dashboard_totals(from_date: Optional[datetime]=Query(None),to_date:Optional[datetime]=Query(None),timezone: Optional[str] = Query("Asia/Kolkata"), session: AsyncSession = Depends(get_pg_db_session)):

    day_expr = func.date(func.timezone('Asia/Kolkata', Orders.created_at))
    profit_expr = (
        ((cast(func.coalesce(Orders.unit_price, 0), Numeric) *
        cast(func.coalesce(Orders.quantity, 0), Numeric)))
        -
        cast(func.coalesce(Orders.final_price, 0), Numeric)
    )
    stmt = select(
        day_expr.label("day"),
        func.count(Orders.id).label("total_orders"),
        func.count().filter(Orders.payment_status == PaymentStatus.NOT_PAID.value).label("pending_dues"),
        func.count().filter(Orders.invoice_status == InvoiceStatus.INCOMPLETED.value).label("pending_invoices"),
        func.round(func.coalesce(func.sum(profit_expr), 0)).label("total_revenue"),
        func.round(func.sum(Orders.final_price)).label("order_value")
    ).where(
        Orders.is_deleted==False
    ).group_by(
        day_expr
    ).order_by(
        day_expr
    )

    if from_date and to_date:
        ic("hello")
        stmt=stmt.where(
            day_expr >= from_date,
            day_expr <= to_date
        )

    datas=(await session.execute(stmt)).mappings().all()
    ic(datas)
    return{'dashboard_datas':datas}



    
    