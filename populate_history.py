import asyncio
from infras.primary_db.main import AsyncLocalSession
from sqlalchemy import text

async def run():
    async with AsyncLocalSession() as session:
        # Populate product_pricing_history
        await session.execute(text("""
            INSERT INTO product_pricing_history (product_id, price, created_at)
            SELECT id, price, created_at FROM products p
            WHERE NOT EXISTS (
                SELECT 1 FROM product_pricing_history h WHERE h.product_id = p.id
            )
        """))
        
        # Populate distributor_discount_history
        await session.execute(text("""
            INSERT INTO distributor_discount_history (distributor_id, discounts, created_at)
            SELECT id, discounts, created_at FROM distributors d
            WHERE NOT EXISTS (
                SELECT 1 FROM distributor_discount_history h WHERE h.distributor_id = d.id
            )
        """))
        
        await session.commit()
        print('Done!')

asyncio.run(run())
