import asyncio
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from core.settings import SETTINGS
import datetime

from infras.primary_db.models.order import Orders, OrdersPaymentInvoiceInfo
from infras.primary_db.models.customer import Customers
from infras.primary_db.models.contact import Contacts
from infras.primary_db.models.product import Products
from infras.primary_db.models.distributor import Distributors

async def main():
    engine = create_async_engine(SETTINGS.PG_DB_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        from infras.primary_db.repos.order_repo import OrdersRepo
        repo = OrdersRepo(session, user_role="ADMIN", cur_user_id="1")
        
        from_date = datetime.date(2000, 1, 1)
        to_date = datetime.date(2030, 1, 1)
        
        res = await repo.get_payment_pending_report(from_date, to_date, owner_name="NAGARAJ D")
        
        import json
        print(json.dumps(res, indent=2))

if __name__ == "__main__":
    asyncio.run(main())
