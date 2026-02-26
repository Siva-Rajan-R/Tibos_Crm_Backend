from pydantic import BaseModel
from typing import Optional,List
from core.data_formats.enums.order_enums import DistributorType
from core.data_formats.typed_dicts.distributor_typdict import DistributorDiscountsTypDict

class CreateDistriSchema(BaseModel):
    name:str
    discounts:List[DistributorDiscountsTypDict]


class UpdateDistriSchema(BaseModel):
    id:str
    name:Optional[str]=None
    discounts:Optional[List[DistributorDiscountsTypDict]]=None

class RecoverDistriSchema(BaseModel):
    distributor_id:str