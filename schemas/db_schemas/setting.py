from pydantic import BaseModel
from typing import Optional


class SettingsDbSchema(BaseModel):
    name:str
    datas:dict
    