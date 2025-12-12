from fastapi import Depends,APIRouter,Query
from database.configs.pg_config import get_pg_db_session,AsyncSession
from api.dependencies.token_verification import verify_user
from typing import Optional
from database.models.pg_models.product import Products
from database.models.pg_models.order import Orders,PaymentStatus,InvoiceStatus
from database.models.pg_models.contact import Contacts
from database.models.pg_models.customer import Customers
from database.models.pg_models.user import Users
from datetime import datetime,date,timedelta
from sqlalchemy import select,func
from typing import Optional
from icecream import ic
import pytz

router=APIRouter(
    tags=['Dashboard']
)


@router.get('/dashboard/weeks')
async def get_dashboard_totals(date: datetime=Query(),timezone: Optional[str] = Query("Asia/Kolkata"), session: AsyncSession = Depends(get_pg_db_session)):
    st_date = date.date()
    end_date = (date + timedelta(days=6)).date()

    day_expr = func.date(func.timezone('Asia/Kolkata', Orders.created_at))

    stmt = select(
        day_expr.label("day"),
        func.count(Orders.id).label("total_orders"),
        func.count().filter(Orders.payment_status == PaymentStatus.NOT_PAID.value).label("pending_dues"),
        func.count().filter(Orders.invoice_status == InvoiceStatus.INCOMPLETED.value).label("pending_invoices"),
        func.sum(Orders.final_price).label("total_revenue")
    ).where(
        day_expr >= st_date,
        day_expr <= end_date
    ).group_by(
        day_expr
    ).order_by(
        day_expr
    )

    datas=(await session.execute(stmt)).mappings().all()
    ic(datas)
    return{'dashboard_datas':datas}



    
    