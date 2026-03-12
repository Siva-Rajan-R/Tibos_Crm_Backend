from core.utils.export_func import create_excel_export
from typing import List,Optional
from pydantic import EmailStr


async def generate_excel_report(
    ctx,
    data_cls,
    data_key:str,
    user_id:str,
    kwargs:dict,
    mapper:dict,
    report_name:str,
    converter_name:str,
    sheet_name:str,
    file_name:str,
    emails_tosend:List[EmailStr],
    custom_fields:Optional[List[str]]=None
):
    await create_excel_export(
        data_cls=data_cls,
        data_key=data_key,
        kwargs=kwargs,
        mapper=mapper,
        user_id=user_id,
        report_name=report_name,
        converter_name=converter_name,
        sheet_name=sheet_name,
        file_name=file_name,
        emails_tosend=emails_tosend,
        custom_fields=custom_fields
    )


