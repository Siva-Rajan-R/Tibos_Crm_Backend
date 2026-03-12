from pydantic import BaseModel
from typing import Optional,List
from .order import OrderFilterSchema


class ExportFields(BaseModel):
    fields:Optional[List[str]]=None
    filters:Optional[OrderFilterSchema]=OrderFilterSchema()
