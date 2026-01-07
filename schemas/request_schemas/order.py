from pydantic import BaseModel,EmailStr
from core.data_formats.typed_dicts.pg_dict import DeliveryInfo
from core.data_formats.enums.pg_enums import PaymentStatus,InvoiceStatus
from typing import Optional

class AddOrderSchema(BaseModel):
    customer_id:str
    product_id:str
    quantity:int
    total_price:float
    discount_price:float
    final_price:float
    delivery_info:DeliveryInfo
    payment_status:PaymentStatus
    invoice_status:InvoiceStatus


class UpdateOrderSchema(BaseModel):
    order_id:str
    customer_id:str
    product_id:str
    quantity:Optional[int]=None
    total_price:Optional[float]=None
    discount_price:Optional[float]=None
    final_price:Optional[float]=None
    delivery_info:Optional[DeliveryInfo]=None
    payment_status:Optional[PaymentStatus]=None
    invoice_status:Optional[InvoiceStatus]=None