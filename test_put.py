import asyncio
from infras.primary_db.main import AsyncLocalSession
from infras.primary_db.models.user import Users
from sqlalchemy import select
from core.utils.token_handler import create_access_token
from infras.primary_db.models.customer import Customers
from infras.primary_db.models.contact import Contacts
from infras.primary_db.models.product import Products

async def run():
    async with AsyncLocalSession() as session:
        user = (await session.execute(select(Users).limit(1))).scalar_one_or_none()
        token = create_access_token({'id': user.id, 'role': user.role, 'email': user.email, 'type': 'access'})
        print('TOKEN=' + token)

asyncio.run(run())
