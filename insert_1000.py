import asyncio
from infras.primary_db.main import AsyncLocalSession
from sqlalchemy import text

async def run():
    async with AsyncLocalSession() as session:
        # Insert the 1000.0 price for the specific product e38f5c96-2e40-5bdc-81e9-62799f75f190
        await session.execute(text("""
            INSERT INTO product_pricing_history (product_id, price, created_at, created_by)
            VALUES ('e38f5c96-2e40-5bdc-81e9-62799f75f190', 1000.0, '2026-06-06 15:00:00+00', (SELECT id FROM users LIMIT 1))
        """))
        await session.commit()
        print("Inserted 1000.0 history")

asyncio.run(run())
