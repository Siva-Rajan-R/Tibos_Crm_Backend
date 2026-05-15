from arq import create_pool
from arq.connections import RedisSettings
from core.settings import SETTINGS
from typing import List

async def enqueue_test_report_job(report_type: str, recipients: List[str]):
    redis = await create_pool(
        RedisSettings.from_dsn(SETTINGS.REDIS_URL)
    )

    await redis.enqueue_job(
        "run_test_report",
        report_type=report_type,
        recipients=recipients
    )
