from typing import Optional,List
from pydantic import BaseModel
from core.data_formats.typed_dicts.distributor_typdict import DistributorPaymentInfosTypDict

class AddDistributorPaymentDbSchema(BaseModel):
    orders:List
    customer_id:str
    distributor_id:str
    renewal_type:str
    payment_infos:List[DistributorPaymentInfosTypDict]

class UpdateDistributorPaymentDbSchema(BaseModel):
    id:int
    payment_infos:List[DistributorPaymentInfosTypDict]
    renewal_type:str