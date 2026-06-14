import asyncio
import os
from infras.primary_db.main import PG_BASE, PG_ENGINE
from infras.primary_db.models.product import ProductPricingHistory
from infras.primary_db.models.distributor import DistributorDiscountHistory

async def main():
    async with PG_ENGINE.begin() as conn:
        await conn.run_sync(PG_BASE.metadata.create_all)
    print("Tables created successfully")

if __name__ == "__main__":
    asyncio.run(main())
