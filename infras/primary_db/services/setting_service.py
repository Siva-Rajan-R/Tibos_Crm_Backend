from ..repos.setting_repo import SettingsRepo
from schemas.db_schemas.setting import SettingsDbSchema
from schemas.request_schemas.setting import EmailSettingSchema, EmailUpdateSchema, ReportScheduleSchema, PendingDuesAlertSchema, PendingDuesAlertTestSchema
from ..models.settings import Settings
from sqlalchemy import update,select,delete,func
from icecream import ic
from schemas.db_schemas.setting import SettingsDbSchema
from security.symm_encryption import SymmetricEncryption
from sqlalchemy.ext.asyncio import AsyncSession
from core.decorators.db_session_handler_dec import start_db_transaction
from models.response_models.req_res_models import ErrorResponseTypDict
from core.utils.uuid_generator import generate_uuid
from core.data_formats.enums.dd_enums import SettingsEnum
from services.email_service import send_email

SECRET_KEY="2j4ju7jzfnQVamDtZfgC1kbhdILKEGFAz5nRL3PdZ-M="

class SettingsService:
    def __init__(self,session:AsyncSession):
        self.session=session

    async def init_settings(self):
        for name in list(SettingsEnum._value2member_map_.values()):
            await SettingsRepo(session=self.session).create(data=SettingsDbSchema(name=name,datas={}))

    async def email_create(self,data:EmailSettingSchema):
        data_toadd=data.model_dump(mode='json')
        print(data_toadd)
        data_toadd['client_secret']=SymmetricEncryption(secret_key=SECRET_KEY).encrypt_data(data=data_toadd['client_secret'])
        data_toadd['id']=generate_uuid()
        data_toadd={data.email:data_toadd}
        db_data=await SettingsRepo(session=self.session).create(data=SettingsDbSchema(name=SettingsEnum.EMAIL.value,datas=data_toadd))
        return db_data
    

    async def email_delete(self, email_id: str):
        return await SettingsRepo(session=self.session).delete_email_by_id(email_id=email_id)

    async def email_update(self, email_id: str, data: EmailUpdateSchema):
        fields = {"email": data.email, "tenant_id": data.tenant_id, "client_id": data.client_id}
        if data.client_secret:
            fields["client_secret"] = SymmetricEncryption(secret_key=SECRET_KEY).encrypt_data(data=data.client_secret)
        return await SettingsRepo(session=self.session).update_email_by_id(email_id=email_id, updated_fields=fields)

    async def pending_dues_alert_test(self, data: PendingDuesAlertTestSchema, client_ip: str):
        category_labels = {
            "tds_pending": "TDS Pending", "not_paid": "Not Paid", "gst_pending": "GST Pending",
            "short_pending": "Short Pending", "half_pending": "Half Pending",
            "pending_invoices": "Pending Invoices", "not_activated": "Not Activated",
        }
        cats_html = "".join(
            f'<span style="background:#fee2e2;color:#b91c1c;padding:3px 10px;border-radius:999px;font-size:12px;font-weight:600;margin:2px;display:inline-block">{category_labels.get(c, c)}</span>'
            for c in data.categories
        )
        body = f"""
        <div style="font-family:sans-serif;max-width:480px;margin:auto;padding:24px;border:1px solid #e5e7eb;border-radius:12px">
          <h2 style="color:#111827;margin-bottom:4px">Pending Dues Alert — Test Email</h2>
          <p style="color:#6b7280;font-size:13px;margin-bottom:16px">This is a test email to verify your alert configuration.</p>
          <p style="font-size:13px;font-weight:600;color:#374151;margin-bottom:8px">Selected Categories ({len(data.categories)}):</p>
          <div style="margin-bottom:16px">{cats_html}</div>
          <p style="color:#9ca3af;font-size:11px">Sent to {len(data.recipients)} recipient(s).</p>
        </div>
        """
        await send_email(
            client_ip=client_ip,
            reciver_emails=data.recipients,
            subject="[Test] Pending Dues Alert Configuration",
            body=body,
            is_html=True,
        )
        return True

    async def report_schedule_upsert(self, data: ReportScheduleSchema):
        datas = data.schedule.model_dump(mode='json')
        return await SettingsRepo(session=self.session).upsert_replace(name=SettingsEnum.REPORT_SCHEDULE.value, datas=datas)

    async def pending_dues_alert_upsert(self, data: PendingDuesAlertSchema):
        datas = data.model_dump(mode='json')
        return await SettingsRepo(session=self.session).upsert_replace(name=SettingsEnum.PENDING_DUES_ALERT.value, datas=datas)

    async def get(self,id:int):
        settings=await SettingsRepo(session=self.session).get(id=id)
        return settings
    
    async def getby_name(self,name:SettingsEnum):
        settings=await SettingsRepo(session=self.session).getby_name(name=name)
        return settings
    
    async def delete(self,setting_id:int,value_id:str):
        is_deleted=await SettingsRepo(session=self.session).delete(setting_id=setting_id,value_id=value_id)

        return is_deleted


