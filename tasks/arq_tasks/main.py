# worker.py
from arq import create_pool
from arq.connections import RedisSettings
from .workers.report import generate_excel_report
from core.settings import SETTINGS



class WorkerSettings:
    functions = [generate_excel_report]

    redis_settings = RedisSettings.from_dsn(SETTINGS.REDIS_URL)

    max_jobs = 10
    job_timeout = 300