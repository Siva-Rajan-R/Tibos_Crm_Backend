# worker.py
import asyncio
from arq import Worker
from arq.connections import RedisSettings
from core.settings import SETTINGS
from tasks.arq_tasks.workers.report import generate_excel_report


async def main():
    worker = Worker(
        functions=[generate_excel_report],
        redis_settings=RedisSettings.from_dsn(SETTINGS.REDIS_URL),
        max_jobs=10,
        job_timeout=300,
    )
    print("✅ Successfully Worker Started")
    await worker.async_run()


if __name__ == "__main__":
    asyncio.run(main())