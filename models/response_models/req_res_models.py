from typing import TypedDict,Optional,Any
from pydantic import BaseModel


class BaseResponseTypDict(BaseModel):
    msg:str
    status_code:int
    success:bool

class SuccessResponseTypDict(BaseModel):
    detail:BaseResponseTypDict
    data:Optional[Any]=None


class ErrorResponseTypDict(BaseResponseTypDict):
    description:str