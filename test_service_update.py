import asyncio
from infras.primary_db.main import AsyncLocalSession
from infras.primary_db.services.product_service import ProductsService
from schemas.db_schemas.product import UpdateProductDbSchema
from core.data_formats.enums.user_enums import UserRoles
from sqlalchemy import text
from infras.primary_db.models.customer import Customers
from infras.primary_db.models.contact import Contacts
from infras.primary_db.models.product import Products

async def run():
    async with AsyncLocalSession() as session:
        # Create an update request
        data = UpdateProductDbSchema(product_id="e38f5c96-2e40-5bdc-81e9-62799f75f190", price=1200.0)
        # Mock user role and ID (use the actual one from DB)
        res = await session.execute(text("SELECT id FROM users LIMIT 1"))
        real_user_id = res.scalar()
        service = ProductsService(session=session, user_role=UserRoles.SUPER_ADMIN, cur_user_id=real_user_id)
        
        res = await service.update(data)
        print("Update result:", res)
        
        # Check history
        history = await session.execute(text("SELECT price, created_at FROM product_pricing_history WHERE product_id='e38f5c96-2e40-5bdc-81e9-62799f75f190' ORDER BY created_at DESC"))
        print("History:", history.fetchall())

asyncio.run(run())
