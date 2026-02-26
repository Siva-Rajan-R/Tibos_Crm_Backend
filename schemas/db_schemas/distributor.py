from pydantic import BaseModel
from typing import Optional,List,Dict
from core.data_formats.enums.order_enums import DistributorType
from core.data_formats.typed_dicts.distributor_typdict import DistributorDiscountsTypDict

class CreateDistriDbSchema(BaseModel):
    lui_id:Optional[str]=None
    id:str
    ui_id:str
    name:str
    discounts:Dict


class UpdateDistriDbSchema(BaseModel):
    id:str
    name:Optional[str]=None
    discounts:Optional[Dict]=None