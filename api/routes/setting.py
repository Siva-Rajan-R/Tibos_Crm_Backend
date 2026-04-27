from fastapi import Depends,APIRouter,Query,File,UploadFile,Form,Request
from schemas.request_schemas.contact import AddContactSchema,UpdateContactSchema,RecoverContactSchema
from infras.primary_db.main import get_pg_db_session,AsyncSession
from api.dependencies.token_verification import verify_user
from ..handlers.contact_handler import HandleContactsRequest
from typing import Optional,Literal
from core.data_formats.enums.dd_enums import ImportExportTypeEnum
from schemas.request_schemas.setting import EmailSettingSchema, EmailUpdateSchema, ReportScheduleSchema, PendingDuesAlertSchema, PendingDuesAlertTestSchema, EmailTemplateSchema
from infras.primary_db.main import AsyncSession,get_pg_db_session
from infras.primary_db.services.setting_service import SettingsService
from core.data_formats.enums.dd_enums import SettingsEnum


router=APIRouter(prefix="/settings",tags=["Settings CRUD"])

@router.post('/email')
async def settings_email(data:EmailSettingSchema,session:AsyncSession=Depends(get_pg_db_session)):
    return await SettingsService(session=session).email_create(data=data)

@router.put('/email/{email_id}')
async def update_email(email_id:str,data:EmailUpdateSchema,session:AsyncSession=Depends(get_pg_db_session)):
    return await SettingsService(session=session).email_update(email_id=email_id,data=data)

@router.delete('/email/{email_id}')
async def delete_email(email_id:str,session:AsyncSession=Depends(get_pg_db_session)):
    return await SettingsService(session=session).email_delete(email_id=email_id)

@router.post('/report-schedule')
async def upsert_report_schedule(data:ReportScheduleSchema,session:AsyncSession=Depends(get_pg_db_session)):
    return await SettingsService(session=session).report_schedule_upsert(data=data)

@router.post('/pending-dues-alert')
async def upsert_pending_dues_alert(data:PendingDuesAlertSchema,session:AsyncSession=Depends(get_pg_db_session)):
    return await SettingsService(session=session).pending_dues_alert_upsert(data=data)

@router.post('/pending-dues-alert/test')
async def test_pending_dues_alert(request:Request,data:PendingDuesAlertTestSchema,session:AsyncSession=Depends(get_pg_db_session)):
    client_ip = request.client.host if request.client else "unknown"
    return await SettingsService(session=session).pending_dues_alert_test(data=data,client_ip=client_ip)

@router.post('/email-template')
async def upsert_email_template(data:EmailTemplateSchema,session:AsyncSession=Depends(get_pg_db_session)):
    return await SettingsService(session=session).email_template_upsert(data=data)

@router.get('/id/{id}')
async def get_settings(id:int,session:AsyncSession=Depends(get_pg_db_session)):
    return await SettingsService(session=session).get(id=id)

@router.get('/name/{name}')
async def get_settings_by_name(name:SettingsEnum,session:AsyncSession=Depends(get_pg_db_session)):
    return await SettingsService(session=session).getby_name(name=name)

