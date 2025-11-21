from pydantic import BaseModel,EmailStr
from data_formats.typed_dicts.pg_dict import DeliveryInfo
from data_formats.enums.pg_enums import PaymentStatus,InvoiceStatus

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
    quantity:int
    total_price:float
    discount_price:float
    final_price:float
    delivery_info:DeliveryInfo
    payment_status:PaymentStatus
    invoice_status:InvoiceStatus