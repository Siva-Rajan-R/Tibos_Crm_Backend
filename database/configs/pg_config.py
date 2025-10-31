from sqlalchemy.ext.asyncio import create_async_engine,async_sessionmaker,AsyncSession
from sqlalchemy.orm import declarative_base
import os
from dotenv import load_dotenv
from icecream import ic
load_dotenv()

PG_DB_URL=os.getenv("PG_DB_URL")

PG_ENGINE=create_async_engine(url=PG_DB_URL)

PG_BASE=declarative_base()

AsyncLocalSession=async_sessionmaker(PG_ENGINE)


async def init_pg_db():
    try:
        ic("🔃 Initializing Pg DB...")
        async with PG_ENGINE.begin() as conn:
            conn.run_sync(PG_BASE.metadata.create_all)
        ic("✅ Pg Database Initialized Successfully")
    except Exception as e:
        ic(f"❌ Error Initializing Pg Database {e}")


async def get_pg_db_session():
    async_session=AsyncLocalSession()
    try:
        yield async_session
    finally:
        await async_session.close()
