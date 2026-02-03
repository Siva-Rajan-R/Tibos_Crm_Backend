from pydantic import BaseModel
from typing import Optional,List

class CreateDistriDbSchema(BaseModel):
    id:str
    name:str
    discount:str


class UpdateDistriDbSchema(BaseModel):
    id:str
    name:Optional[str]=None
    discount:Optional[str]=None