from sqlalchemy.ext.asyncio import create_async_engine,async_sessionmaker,AsyncSession
from sqlalchemy.orm import declarative_base
import os
from core.settings import SETTINGS
from icecream import ic

PG_ENGINE=create_async_engine(url=SETTINGS.PG_DB_URL)

PG_BASE=declarative_base()

AsyncLocalSession=async_sessionmaker(PG_ENGINE,class_=AsyncSession,expire_on_commit=False)


async def init_pg_db():
    try:
        ic("🔃 Initializing Pg DB...")
        async with PG_ENGINE.begin() as conn:
            await conn.run_sync(PG_BASE.metadata.create_all)
            await conn.commit()
        ic("✅ Pg Database Initialized Successfully")
    except Exception as e:
        ic(f"❌ Error Initializing Pg Database {e}")


async def get_pg_db_session():
    async_session=AsyncLocalSession()
    try:
        yield async_session
    finally:
        await async_session.close()
