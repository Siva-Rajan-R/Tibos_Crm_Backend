from typing import Optional,List
from pydantic import BaseModel
from core.data_formats.typed_dicts.distributor_typdict import DistributorPaymentInfosTypDict

class AddDbDistributorPaymentSchema(BaseModel):
    order_id:str
    payment_infos:List[DistributorPaymentInfosTypDict]

class UpdateDbDistributorPaymentSchema(BaseModel):
    id:int
    payment_infos:List[DistributorPaymentInfosTypDict]