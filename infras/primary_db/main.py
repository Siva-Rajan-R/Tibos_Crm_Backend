from sqlalchemy.ext.asyncio import create_async_engine,async_sessionmaker,AsyncSession
from sqlalchemy.orm import declarative_base
from sqlalchemy import text
import os,asyncio
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
            # lightweight migrations for columns added after the table was first created
            await conn.execute(text("ALTER TABLE products ADD COLUMN IF NOT EXISTS financial_year INTEGER"))
            # backfill FY from names like '... FY-2026' / 'fy 2026' ((?i) = case-insensitive match)
            await conn.execute(text(
                r"UPDATE products SET financial_year=CAST(substring(name from '(?i)\mfy[- ]?([0-9]{4})') AS INTEGER) "
                r"WHERE financial_year IS NULL AND name ~* '\mfy[- ]?[0-9]{4}'"
            ))
            # products that don't mention any FY belong to the old 2025 pricing year
            await conn.execute(text("UPDATE products SET financial_year=2025 WHERE financial_year IS NULL"))
            # freshworks-style lead qualification fields
            await conn.execute(text("ALTER TABLE leads ADD COLUMN IF NOT EXISTS company VARCHAR"))
            await conn.execute(text("ALTER TABLE leads ADD COLUMN IF NOT EXISTS job_title VARCHAR"))
            await conn.execute(text("ALTER TABLE leads ADD COLUMN IF NOT EXISTS rating VARCHAR"))
            await conn.execute(text("ALTER TABLE leads ADD COLUMN IF NOT EXISTS expected_value FLOAT"))
            await conn.execute(text("ALTER TABLE leads ADD COLUMN IF NOT EXISTS city VARCHAR"))
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
