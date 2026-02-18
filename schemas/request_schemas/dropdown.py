from pydantic import BaseModel
from typing import List


class AddDropDownSchema(BaseModel):
    name:str
    values:List[str]

class UpdateDropDownSchema(BaseModel):
    name:str
    values:List[str]