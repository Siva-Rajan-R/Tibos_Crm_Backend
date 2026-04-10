from typing import Optional,List
from pydantic import BaseModel
from core.data_formats.typed_dicts.distributor_typdict import DistributorPaymentInfosTypDict

class AddDistributorPaymentSchema(BaseModel):
    orders:List
    customer_id:str
    distributor_id:str
    renewal_type:str
    payment_infos:List[DistributorPaymentInfosTypDict]

class UpdateDistributorPaymentSchema(BaseModel):
    id:int
    customer_id:str
    distributor_id:str
    renewal_type:str
    payment_infos:List[DistributorPaymentInfosTypDict]

class RecoverDistributorPayment(BaseModel):
    distributor_payment_id:int