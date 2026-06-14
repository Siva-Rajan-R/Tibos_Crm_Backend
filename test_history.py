import asyncio
from infras.primary_db.main import AsyncLocalSession
from sqlalchemy import text

async def run():
    async with AsyncLocalSession() as session:
        res = await session.execute(text("SELECT price FROM product_pricing_history WHERE product_id='e38f5c96-2e40-5bdc-81e9-62799f75f190' ORDER BY created_at DESC"))
        print(res.fetchall())

asyncio.run(run())
