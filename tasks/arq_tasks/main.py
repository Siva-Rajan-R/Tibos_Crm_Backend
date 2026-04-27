# worker.py
import asyncio
from arq import Worker, cron
from arq.connections import RedisSettings
from core.settings import SETTINGS
from tasks.arq_tasks.workers.report import generate_excel_report
from tasks.arq_tasks.workers.alert import send_pending_dues_alert, send_report_schedule


async def main():
    worker = Worker(
        functions=[generate_excel_report],
        cron_jobs=[
            # runs every minute at second :00 — each function checks internally
            # whether the configured HH:MM matches before doing anything
            cron(send_pending_dues_alert, second=0),
            cron(send_report_schedule, second=0),
        ],
        redis_settings=RedisSettings.from_dsn(SETTINGS.REDIS_URL),
        max_jobs=10,
        job_timeout=300,
    )
    print("✅ Successfully Worker Started")
    await worker.async_run()


if __name__ == "__main__":
    asyncio.run(main())