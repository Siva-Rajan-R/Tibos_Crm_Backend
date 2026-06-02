import asyncio
from infras.primary_db.main import AsyncLocalSession
from infras.primary_db.repos.activity_log_repo import ActivityLogRepo
from core.data_formats.enums.user_enums import UserRoles
from sqlalchemy.ext.asyncio import AsyncSession

async def test():
    async with AsyncLocalSession() as session:
        repo = ActivityLogRepo(session, UserRoles.SUPER_ADMIN, "123")
        res = await repo.get(from_date="2026-05-31", to_date="2026-05-31")
        print(f"Total results: {len(res)}")
        for r in res:
            print(f"ID: {r['id']}, Date: {r['created_at']}")

asyncio.run(test())
