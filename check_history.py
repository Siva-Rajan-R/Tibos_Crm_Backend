import asyncio
from infras.primary_db.main import AsyncLocalSession
from sqlalchemy import text
from infras.primary_db.models.customer import Customers
from infras.primary_db.models.contact import Contacts
from infras.primary_db.models.product import Products

async def run():
    async with AsyncLocalSession() as session:
        res = await session.execute(text("SELECT price FROM products WHERE id='e38f5c96-2e40-5bdc-81e9-62799f75f190'"))
        print('CURRENT PRICE:', res.scalar())

asyncio.run(run())
