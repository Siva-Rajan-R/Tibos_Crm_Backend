import asyncio
from infras.primary_db.main import AsyncLocalSession
from infras.primary_db.models.user import Users
from sqlalchemy import select

async def run():
    async with AsyncLocalSession() as s:
        res = await s.execute(select(Users.id, Users.email, Users.name))
        for row in res.all():
            print(f"ID: {row.id}, Email: {row.email}, Name: {row.name}")

if __name__ == "__main__":
    asyncio.run(run())
