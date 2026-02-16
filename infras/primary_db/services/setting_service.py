from ..repos.setting_repo import SettingsRepo
from schemas.db_schemas.setting import SettingsDbSchema
from schemas.request_schemas.setting import EmailSettingSchema
from ..models.settings import Settings
from sqlalchemy import update,select,delete,func
from icecream import ic
from schemas.db_schemas.setting import SettingsDbSchema
from security.symm_encryption import SymmetricEncryption
from sqlalchemy.ext.asyncio import AsyncSession
from core.decorators.db_session_handler_dec import start_db_transaction
from models.response_models.req_res_models import ErrorResponseTypDict
from core.utils.uuid_generator import generate_uuid
from core.data_formats.enums.common_enums import SettingsEnum

SECRET_KEY="2j4ju7jzfnQVamDtZfgC1kbhdILKEGFAz5nRL3PdZ-M="

class SettingsService:
    def __init__(self,session:AsyncSession):
        self.session=session

    async def init_settings(self):
        for name in list(SettingsEnum._value2member_map_.values()):
            await SettingsRepo(session=self.session).create(data=SettingsDbSchema(name=name,datas={}))

    async def email_create(self,data:EmailSettingSchema):
        data_toadd=data.model_dump(mode='json')
        data_toadd['client_secret']=SymmetricEncryption(secret_key=SECRET_KEY).encrypt_data(data=data_toadd['client_secret'])
        data_toadd['id']=generate_uuid()
        data_toadd={data_toadd['id']:data_toadd}
        db_data=await SettingsRepo(session=self.session).create(data=SettingsDbSchema(name=SettingsEnum.EMAIL.value,datas=data_toadd))
        return db_data
    

    async def get(self,id:int):
        settings=await SettingsRepo(session=self.session).get(id=id)
        return settings
    
    async def getby_name(self,name:SettingsEnum):
        settings=await SettingsRepo(session=self.session).getby_name(name=name)
        return settings
    
    async def delete(self,setting_id:int,value_id:str):
        is_deleted=await SettingsRepo(session=self.session).delete(setting_id=setting_id,value_id=value_id)

        return is_deleted


