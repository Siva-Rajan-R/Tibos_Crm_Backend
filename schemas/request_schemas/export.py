from pydantic import BaseModel
from typing import Optional,List


class ExportFields(BaseModel):
    fields:Optional[List[str]]=None