from typing import Optional,List
from pydantic import BaseModel
from core.data_formats.typed_dicts.distributor_typdict import DistributorPaymentInfosTypDict

class AddDistributorPaymentSchema(BaseModel):
    order_id:str
    payment_infos:List[DistributorPaymentInfosTypDict]
    payment_type:str

class UpdateDistributorPaymentSchema(BaseModel):
    id:int
    order_id:str
    payment_infos:List[DistributorPaymentInfosTypDict]
    payment_type:str

class RecoverDistributorPayment(BaseModel):
    distributor_payment_id:int