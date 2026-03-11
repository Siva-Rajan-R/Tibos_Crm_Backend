from ..workers.report import generate_excel_report
from arq import create_pool
from arq.connections import RedisSettings
from core.settings import SETTINGS
from typing import Optional,List
from pydantic import EmailStr

async def enqueue_excel_report_job(
        data_cls,
        user_id:str,
        data_key:str,
        mapper:dict,
        report_name:str,
        converter_name:str,
        sheet_name:str,
        file_name:str,
        emails_tosend:List[EmailStr],
        custom_fields:Optional[List[str]]=None
):
    redis = await create_pool(
        RedisSettings.from_dsn(SETTINGS.REDIS_URL)
    )

    await redis.enqueue_job(
        "generate_excel_report",
        data_cls=data_cls,
        user_id=user_id,
        data_key=data_key,
        mapper=mapper,
        report_name=report_name,
        converter_name=converter_name,
        sheet_name=sheet_name,
        file_name=file_name,
        emails_tosend=emails_tosend,
        custom_fields=custom_fields
    )
