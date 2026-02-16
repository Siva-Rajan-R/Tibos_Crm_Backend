from fastapi import Depends,APIRouter,Query,File,UploadFile,Form
from schemas.request_schemas.contact import AddContactSchema,UpdateContactSchema,RecoverContactSchema
from infras.primary_db.main import get_pg_db_session,AsyncSession
from api.dependencies.token_verification import verify_user
from ..handlers.contact_handler import HandleContactsRequest
from typing import Optional,Literal
from core.data_formats.enums.common_enums import ImportExportTypeEnum
from schemas.request_schemas.setting import EmailSettingSchema
from infras.primary_db.main import AsyncSession,get_pg_db_session
from infras.primary_db.services.setting_service import SettingsService
from core.data_formats.enums.common_enums import SettingsEnum


router=APIRouter(prefix="/settings",tags=["Settings CRUD"])

@router.post('/email')
async def settings_email(data:EmailSettingSchema,session:AsyncSession=Depends(get_pg_db_session)):
    return await SettingsService(session=session).email_create(data=data)

@router.get('/id/{id}')
async def get_settings(id:int,session:AsyncSession=Depends(get_pg_db_session)):
    return await SettingsService(session=session).get(id=id)

@router.get('/name/{name}')
async def get_settings_by_name(name:SettingsEnum,session:AsyncSession=Depends(get_pg_db_session)):
    return await SettingsService(session=session).getby_name(name=name)

