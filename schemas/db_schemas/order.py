from pydantic import BaseModel,EmailStr
from core.data_formats.typed_dicts.order_typdict import LogisticsInfo,StatusInfo,DeliveryInfo
from typing import Optional
from datetime import date

class AddOrderDbSchema(BaseModel):
    lui_id:Optional[str]=None
    id:str
    ui_id:str
    customer_id:str
    product_id:str
    distributor_id:str
    quantity:int
    additional_discount:str
    unit_price:float
    delivery_info:DeliveryInfo
    status_info:StatusInfo
    logistic_info:LogisticsInfo
    vendor_commision:Optional[str]=None

class UpdateOrderDbSchema(BaseModel):
    order_id:str
    customer_id:str
    product_id:str
    distributor_id:Optional[str]=None
    quantity:Optional[int]=None
    additional_discount:Optional[str]=None
    unit_price:Optional[float]=None
    delivery_info:Optional[DeliveryInfo]=None
    status_info:Optional[StatusInfo]=None
    logistic_info:Optional[LogisticsInfo]=None
    vendor_commision:Optional[str]=None