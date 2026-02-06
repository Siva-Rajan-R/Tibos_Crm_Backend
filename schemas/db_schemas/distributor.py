from pydantic import BaseModel
from typing import Optional,List

class CreateDistriDbSchema(BaseModel):
    lui_id:Optional[str]=None
    id:str
    ui_id:str
    name:str
    discount:str


class UpdateDistriDbSchema(BaseModel):
    id:str
    name:Optional[str]=None
    discount:Optional[str]=None