from models.import_export_models.exports.excel_headings_mapper import ACCOUNTS_MAPPER,CONTACTS_MAPPER,PRODUCTS_MAPPER,DISTRI_MAPPER,ORDERS_MAPPER
from infras.primary_db.repos.customer_repo import CustomersRepo
from infras.primary_db.repos.contact_repo import ContactsRepo
from infras.primary_db.repos.product_repo import ProductsRepo
from infras.primary_db.repos.distri_repo import DistributorsRepo
from infras.primary_db.repos.order_repo import OrdersRepo
from models.repo_models.base_model import BaseRepoModel
from .convert_data_to_excel import convert_data_to_excel_format
from infras.primary_db.main import AsyncLocalSession
from core.data_formats.enums.user_enums import UserRoles
from .generate_excel_data import init_excel,append_excel_rows
from services.email_service import send_email
from .msgraph_attachments import delete_graph_attachment_file
from pydantic import EmailStr
from typing import List,Optional
from schemas.request_schemas.order import OrderFilterSchema
from pathlib import Path
from core.utils.msblob import upload_excel_to_blob,generate_sas_url
from icecream import ic
from templates.email.report import get_report_download_email_content


async def create_excel_export(
        data_cls,
        data_key:str,
        mapper:dict,
        report_name:str,
        converter_name:str,
        sheet_name:str,
        file_name:str,
        emails_tosend:List[EmailStr],
        custom_fields:Optional[List[str]]=None
):
    async with AsyncLocalSession() as session:
        CHUNK_SIZE=500
        OFFSET=1

        if custom_fields and len(mapper)!=len(custom_fields):
            temp_mapper={}
            for key,val in mapper.items():
                if val in custom_fields:
                    temp_mapper[key]=val
            mapper=temp_mapper
        wb, ws=init_excel(sheet_name=sheet_name)
        write_header = True
        while True:
            if OFFSET is not None:
                data=(await data_cls(session=session,user_role=UserRoles.SUPER_ADMIN,cur_user_id="").get(cursor=OFFSET,limit=CHUNK_SIZE))
                ic("data-1",data)
            if not OFFSET or not data[data_key] or len(data[data_key])<1:
                break
            
            converted_data=convert_data_to_excel_format(mapper=mapper,data=data[data_key],converter_name=converter_name)
            ic(converted_data)
            append_excel_rows(ws=ws,datas=converted_data,write_header=write_header)
            OFFSET=data['next_cursor']
            write_header=False

        wb.save(filename=file_name)
        blob_name=upload_excel_to_blob(local_file_path=file_name)
        url=generate_sas_url(blob_name=blob_name)
        ic(url)
        email_content=get_report_download_email_content(user_email=emails_tosend[0],report_name=report_name,record_count=1,download_link=url,footer_image_url="https://tiboscrmstorage.blob.core.windows.net/tibos-crm-static-assets/tibos-logo.png")
        is_email_sended=await send_email(
            client_ip="127.0.0.1",
            reciver_emails=emails_tosend,
            subject=report_name,
            body=email_content,
            is_html=True,
            sender_email_id="crm@tibos.in"
        )

        delete_graph_attachment_file(file_path=file_name)

        ic("Successfully excel generated and sent to the email")


