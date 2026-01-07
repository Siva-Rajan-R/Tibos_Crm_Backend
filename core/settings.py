from pydantic_settings import BaseSettings
from pydantic import EmailStr
from .data_formats.enums.common_enums import EnvironmentEnum
from typing import List,Dict
from .configs.settings_config import init_settings
from dotenv import load_dotenv
from icecream import ic
load_dotenv()


class TibosCrmSettings(BaseSettings):
    ENVIRONMENT:EnvironmentEnum
    DEFAULT_SUPERADMIN_INFO:List[Dict]
    FRONTEND_URL:str

    SYMME_KEY:str

    ACCESS_JWT_KEY:str
    REFRESH_JWT_KEY:str
    JWT_ALG:str

    DEB_AUTH_APIKEY:str
    DEB_AUTH_CLIENT_SECRET:str

    SMTP_SERVER:str
    SMTP_PORT:int
    SENDER_EMAIL:EmailStr
    EMAIL_PASSWORD:str

    FASTSMS_APIKEY:str
    DEB_EMAIL_APIKEY:str
    DEB_EMAIL_URL:str

    REDIS_URL:str
    PG_DB_URL:str

    model_config={
        'case_sensitive':False
    }


SETTINGS:TibosCrmSettings=init_settings(settings=TibosCrmSettings,service_name="Tibos-CRM",env_prefix='')