from ..models.settings import Settings
from sqlalchemy import update,select,delete,func
from sqlalchemy.dialects.postgresql import insert
from icecream import ic
from schemas.db_schemas.setting import SettingsDbSchema
from security.symm_encryption import SymmetricEncryption
from sqlalchemy.ext.asyncio import AsyncSession
from core.decorators.db_session_handler_dec import start_db_transaction
from models.response_models.req_res_models import ErrorResponseTypDict
from core.utils.uuid_generator import generate_uuid
from schemas.request_schemas.setting import EmailSettingSchema
from core.data_formats.enums.common_enums import SettingsEnum



class SettingsRepo():
    def __init__(self,session:AsyncSession):
        self.session=session

    @start_db_transaction
    async def create(self, data: SettingsDbSchema):
        stmt = (
            insert(Settings)
            .values(
                name=data.name,
                datas=data.datas
            )
            .on_conflict_do_update(
                index_elements=[Settings.name],
                set_={
                    "datas": Settings.datas.op("||")(data.datas)
                }
            )
        )

        await self.session.execute(stmt)
        return True
        
    
    async def get(self,id:int):
        stmt=(
            select(
                Settings.id,
                Settings.name,
                Settings.datas
            ).where(
                Settings.id==id
            )
        )

        settings=(await self.session.execute(stmt)).mappings().all()

        return {'settings':settings}
    
    async def getby_name(self,name:SettingsEnum):
        stmt=(
            select(
                Settings.id,
                Settings.name,
                Settings.datas
            ).where(
                Settings.name==name.value
            )
        )

        settings=(await self.session.execute(stmt)).mappings().all()

        return {'settings':settings}
    
    async def delete(self,setting_id:int,value_id:str):
        exists_data=self.get(id=setting_id)['settings']
        del exists_data[value_id]
        stmt=update(Settings).where(Settings.id==setting_id).values(datas=exists_data).returning(Settings.id)
        is_updated=(await self.session.execute(stmt)).scalar_one_or_none()

        return is_updated if is_updated else ErrorResponseTypDict(msg="Error : Deleing setting",status_code=400,success=False,description="Invalid Setting id")
        