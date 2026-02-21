from models.import_export_models.exports.excel_headings_mapper import ACCOUNTS_MAPPER,CONTACTS_MAPPER,PRODUCTS_MAPPER,DISTRI_MAPPER,ORDERS_MAPPER
from infras.primary_db.repos.customer_repo import CustomersRepo
from infras.primary_db.repos.contact_repo import ContactsRepo
from infras.primary_db.repos.product_repo import ProductsRepo
from infras.primary_db.repos.distri_repo import DistributorsRepo
from infras.primary_db.repos.order_repo import OrdersRepo
from .convert_data_to_excel import convert_data_to_excel_format
from infras.primary_db.main import AsyncLocalSession
from core.data_formats.enums.user_enums import UserRoles
from .generate_excel_data import generate_excel
from services.email_service import send_email
from .msgraph_attachments import delete_graph_attachment_file
from pydantic import EmailStr
from typing import List
from schemas.request_schemas.order import OrderFilterSchema



async def create_customer_excel_export(emails_tosend:List[EmailStr]):
    file_path,sheet_name='accounts.xlsx','Accounts'
    async with AsyncLocalSession() as session:
        CHUNK_SIZE=500
        OFFSET=1
        HANDWRITTEN=False
        custome_obj=CustomersRepo(session=session,user_role=UserRoles.SUPER_ADMIN,cur_user_id="")
        while True:
            if OFFSET is not None:
                data=(await custome_obj.get(cursor=OFFSET,limit=CHUNK_SIZE))
            if not OFFSET or not data['customers'] or len(data['customers'])<1:
                is_email_sended=await send_email(
                    client_ip="127.0.0.1",
                    reciver_emails=emails_tosend,
                    subject="Accounts Export",
                    body="<h3>Excel attached</h3>",
                    is_html=True,
                    attachments=[file_path],
                    sender_email_id="order@tibos.in"
                )
                if is_email_sended:
                    delete_graph_attachment_file(file_path=file_path)
                break
            
            converted_data=convert_data_to_excel_format(mapper=ACCOUNTS_MAPPER,data=data['customers'],converter_name="accounts")
            generate_excel(file_path=file_path,sheet_name=sheet_name,handwritten=HANDWRITTEN,datas=converted_data)
            OFFSET=data['next_cursor']
            HANDWRITTEN=True


async def create_contact_excel_export(emails_tosend:List[EmailStr]):
    file_path,sheet_name='contacts.xlsx','Contacts'
    async with AsyncLocalSession() as session:
        CHUNK_SIZE=500
        OFFSET=1
        HANDWRITTEN=False
        contact_obj=ContactsRepo(session=session,user_role=UserRoles.SUPER_ADMIN,cur_user_id="")
        while True:
            if OFFSET is not None:
                data=(await contact_obj.get(cursor=OFFSET,limit=CHUNK_SIZE))
            if not OFFSET or not data['contacts'] or len(data['contacts'])<1:
                is_email_sended=await send_email(
                    client_ip="127.0.0.1",
                    reciver_emails=emails_tosend,
                    subject="Contacts Export",
                    body="<h3>Excel attached</h3>",
                    is_html=True,
                    attachments=[file_path],
                    sender_email_id="order@tibos.in"
                )
                if is_email_sended:
                    delete_graph_attachment_file(file_path=file_path)
                break
            
            converted_data=convert_data_to_excel_format(mapper=CONTACTS_MAPPER,data=data['contacts'],converter_name="contacts")
            generate_excel(file_path=file_path,sheet_name=sheet_name,handwritten=HANDWRITTEN,datas=converted_data)
            OFFSET=data['next_cursor']
            HANDWRITTEN=True


async def create_product_excel_export(emails_tosend:List[EmailStr]):
    file_path,sheet_name='products.xlsx','Products'
    async with AsyncLocalSession() as session:
        CHUNK_SIZE=500
        OFFSET=1
        HANDWRITTEN=False
        product_obj=ProductsRepo(session=session,user_role=UserRoles.SUPER_ADMIN,cur_user_id="")
        while True:
            if OFFSET is not None:
                data=(await product_obj.get(cursor=OFFSET,limit=CHUNK_SIZE))
            if not OFFSET or not data['products'] or len(data['products'])<1:
                is_email_sended=await send_email(
                    client_ip="127.0.0.1",
                    reciver_emails=emails_tosend,
                    subject="products Export",
                    body="<h3>Excel attached</h3>",
                    is_html=True,
                    attachments=[file_path],
                    sender_email_id="order@tibos.in"
                )
                if is_email_sended:
                    delete_graph_attachment_file(file_path=file_path)
                break
            
            converted_data=convert_data_to_excel_format(mapper=PRODUCTS_MAPPER,data=data['products'],converter_name="products")
            generate_excel(file_path=file_path,sheet_name=sheet_name,handwritten=HANDWRITTEN,datas=converted_data)
            OFFSET=data['next_cursor']
            HANDWRITTEN=True

async def create_distri_excel_export(emails_tosend:List[EmailStr]):
    file_path,sheet_name='distributors.xlsx','Distributors'
    async with AsyncLocalSession() as session:
        CHUNK_SIZE=500
        OFFSET=1
        HANDWRITTEN=False
        distributor_obj=DistributorsRepo(session=session,user_role=UserRoles.SUPER_ADMIN,cur_user_id="")
        while True:
            if OFFSET is not None:
                data=(await distributor_obj.get(cursor=OFFSET,limit=CHUNK_SIZE))
            if not OFFSET or not data['distributors'] or len(data['distributors'])<1:
                is_email_sended=await send_email(
                    client_ip="127.0.0.1",
                    reciver_emails=emails_tosend,
                    subject="Distributors Export",
                    body="<h3>Excel attached</h3>",
                    is_html=True,
                    attachments=[file_path],
                    sender_email_id="order@tibos.in"
                )
                if is_email_sended:
                    delete_graph_attachment_file(file_path=file_path)
                break
            
            converted_data=convert_data_to_excel_format(mapper=DISTRI_MAPPER,data=data['distributors'],converter_name="distributors")
            generate_excel(file_path=file_path,sheet_name=sheet_name,handwritten=HANDWRITTEN,datas=converted_data)
            OFFSET=data['next_cursor']
            HANDWRITTEN=True


async def create_order_excel_export(emails_tosend:List[EmailStr]):
    file_path,sheet_name='orders.xlsx','Orders'
    async with AsyncLocalSession() as session:
        CHUNK_SIZE=500
        OFFSET=1
        HANDWRITTEN=False
        order_obj=OrdersRepo(session=session,user_role=UserRoles.SUPER_ADMIN,cur_user_id="")
        filters=OrderFilterSchema()
        while True:
            if OFFSET is not None:
                data=(await order_obj.get(cursor=OFFSET,limit=CHUNK_SIZE,filter=filters))
            if not OFFSET or not data['orders'] or len(data['orders'])<1:
                is_email_sended=await send_email(
                    client_ip="127.0.0.1",
                    reciver_emails=emails_tosend,
                    subject="Orders Export",
                    body="<h3>Excel attached</h3>",
                    is_html=True,
                    attachments=[file_path],
                    sender_email_id="order@tibos.in"
                )
                if is_email_sended:
                    delete_graph_attachment_file(file_path=file_path)
                break
            
            converted_data=convert_data_to_excel_format(mapper=ORDERS_MAPPER,data=data['orders'],converter_name="orders")
            generate_excel(file_path=file_path,sheet_name=sheet_name,handwritten=HANDWRITTEN,datas=converted_data)
            OFFSET=data['next_cursor']
            HANDWRITTEN=True

