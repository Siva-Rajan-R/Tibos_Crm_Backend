from pydantic import BaseModel,EmailStr
from core.data_formats.typed_dicts.pg_dict import DeliveryInfo
from core.data_formats.enums.pg_enums import PaymentStatus,InvoiceStatus,PurchaseTypes,RenewalTypes,DistributorType
from typing import Optional
from datetime import date

class AddOrderSchema(BaseModel):
    customer_id:str
    product_id:str
    distributor_id:str
    quantity:int
    total_price:float
    discount:str
    final_price:float
    unit_price:float
    delivery_info:DeliveryInfo
    payment_status:PaymentStatus
    invoice_status:InvoiceStatus
    invoice_number:Optional[str]=None
    invoice_date:Optional[date]=None
    purchase_type:PurchaseTypes
    renewal_type:RenewalTypes
    bill_to:Optional[str]=None
    vendor_commision:Optional[str]=None
    distributor_type:DistributorType


class UpdateOrderSchema(BaseModel):
    order_id:str
    customer_id:str
    product_id:str
    unit_price:Optional[float]=None
    distributor_id:Optional[str]=None
    quantity:Optional[int]=None
    total_price:Optional[float]=None
    discount:Optional[str]=None
    final_price:Optional[float]=None
    delivery_info:Optional[DeliveryInfo]=None
    payment_status:Optional[PaymentStatus]=None
    invoice_status:Optional[InvoiceStatus]=None
    invoice_number:Optional[str]=None
    invoice_date:Optional[date]=None
    purchase_type:Optional[PurchaseTypes]=None
    renewal_type:Optional[RenewalTypes]=None
    bill_to:Optional[str]=None
    vendor_commision:Optional[str]=None
    distributor_type:Optional[DistributorType]=None

class RecoverOrderSchema(BaseModel):
    order_id:str
    customer_id:str