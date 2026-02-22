from azure.storage.blob import BlobServiceClient
from azure.storage.blob import (
    generate_blob_sas,
    BlobSasPermissions
)
import os
from datetime import datetime,timedelta,timezone
from core.settings import SETTINGS

CONTAINER_NAME = "tibos-crm-excel-exports"

blob_service_client = BlobServiceClient.from_connection_string(SETTINGS.AZURE_STORAGE_CONNECTION_STRING)

def upload_excel_to_blob(local_file_path: str) -> str:
    file_name=local_file_path.split('.')[0]
    cur_time=str(datetime.now().time()).split(':')
    blob_name = f"{file_name}-{datetime.now().date()}-{cur_time[0]}:{cur_time[1]}.xlsx"

    blob_client = blob_service_client.get_blob_client(
        container=CONTAINER_NAME,
        blob=blob_name,
    )

    with open(local_file_path, "rb") as f:
        blob_client.upload_blob(f, overwrite=True)

    return blob_name



def generate_sas_url(blob_name: str, hours: int = 24) -> str:
    account_name = blob_service_client.account_name
    account_key = blob_service_client.credential.account_key

    sas_token = generate_blob_sas(
        account_name=account_name,
        container_name=CONTAINER_NAME,
        blob_name=blob_name,
        account_key=account_key,
        permission=BlobSasPermissions(read=True),
        expiry=datetime.now(tz=timezone.utc) + timedelta(hours=hours),
    )

    return (
        f"https://{account_name}.blob.core.windows.net/"
        f"{CONTAINER_NAME}/{blob_name}?{sas_token}"
    )