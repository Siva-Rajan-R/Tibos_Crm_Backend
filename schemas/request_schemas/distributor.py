from pydantic import BaseModel
from typing import Optional,List

class CreateDistriSchema(BaseModel):
    name:str
    discount:str


class UpdateDistriSchema(BaseModel):
    id:str
    name:Optional[str]=None
    discount:Optional[str]=None

class RecoverDistriSchema(BaseModel):
    distributor_id:str