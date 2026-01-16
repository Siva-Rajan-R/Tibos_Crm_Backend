from pydantic import BaseModel
from typing import Optional,List

class CreateDistriSchema(BaseModel):
    name:str
    product_id:str
    discount:str


class UpdateDistriSchema(BaseModel):
    id:str
    name:Optional[str]=None
    product_id:Optional[str]=None
    discount:Optional[str]=None