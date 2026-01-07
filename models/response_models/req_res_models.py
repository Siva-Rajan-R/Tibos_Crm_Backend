from typing import TypedDict,Optional,Any


class BaseResponseTypDict(TypedDict):
    msg:str
    status_code:int
    success:bool

class SuccessResponseTypDict(TypedDict):
    detail:BaseResponseTypDict
    data:Optional[Any]=None

class ErrorResponseTypDict(BaseResponseTypDict,TypedDict):
    description:str