from pydantic import BaseModel,EmailStr
from core.data_formats.typed_dicts.order_typdict import LogisticsInfo,StatusInfo,DeliveryInfo,CartOrderQtyUpdate
from typing import Optional,List,Literal
from datetime import date


class AddOrderDbSchema(BaseModel):
    lui_id:Optional[str]=None
    id:str
    ui_id:str
    customer_id:str
    product_id:str
    distributor_id:str
    discount_id:str
    quantity:int
    activated:bool
    additional_price:Optional[int]=None
    additional_discount:str
    unit_price:float
    delivery_info:DeliveryInfo
    status_info:List[StatusInfo]
    logistic_info:LogisticsInfo
    vendor_commision:Optional[str]=None

class UpdateOrderDbSchema(BaseModel):
    order_id:str
    customer_id:str
    product_id:str
    activated:Optional[bool]=None
    distributor_id:Optional[str]=None
    discount_id:Optional[str]=None
    quantity:Optional[int]=None
    additional_price:Optional[int]=None
    additional_discount:Optional[str]=None
    unit_price:Optional[float]=None
    delivery_info:Optional[DeliveryInfo]=None
    status_info:Optional[List[StatusInfo]]=None
    logistic_info:Optional[LogisticsInfo]=None
    vendor_commision:Optional[str]=None

class OrderBulkDeleteDbSchema(BaseModel):
    order_ids:List[str]


class AddCartOrderProductDbSchema(BaseModel):
    order_id:str
    product_id:str
    discount_id:str
    additional_price:float
    additional_discount:str
    quantity:int
    unit_price:float
    vendor_commision:Optional[str]=None

class AddCartOrderDbSchema(BaseModel):
    id:str
    ui_id:str
    customer_id:str
    distributor_id:str
    activated:bool
    delivery_info:DeliveryInfo
    status_info:List[StatusInfo]
    logistic_info:LogisticsInfo


class UpdateCartOrderQuantityDbSchema(BaseModel):
    order_id:str
    products:List[CartOrderQtyUpdate]
    type:Literal["EXISTING-ADD-ON"]

class UpdateCartOrderProductDbSchema(BaseModel):
    order_id:str
    product_id:str
    discount_id:str
    additional_price:float
    additional_discount:str
    unit_price:float
    vendor_commision:Optional[str]=None

class UpdateCartOrderDbSchema(BaseModel):
    order_id:str
    customer_id:str
    distributor_id:str
    activated:bool
    delivery_info:DeliveryInfo
    status_info:List[StatusInfo]
    logistic_info:LogisticsInfo