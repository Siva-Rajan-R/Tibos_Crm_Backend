from pydantic import BaseModel,EmailStr
from core.data_formats.typed_dicts.order_typdict import LogisticsInfo,StatusInfo,DeliveryInfo
from core.data_formats.enums.order_enums import InvoiceStatus,PaymentStatus,RenewalTypes,PurchaseTypes,DistributorType,OrderFilterRevenueEnum
from typing import Optional,Union,List
from datetime import date
from core.data_formats.typed_dicts.order_typdict import OrderDateFilterTypDict

class AddOrderSchema(BaseModel):
    customer_id:str
    product_id:str
    distributor_id:str
    discount_id:str
    quantity:int
    activated:bool
    additional_discount:str
    additional_price:Optional[int]=None
    unit_price:float
    delivery_info:DeliveryInfo
    status_info:List[StatusInfo]
    logistic_info:LogisticsInfo
    vendor_commision:Optional[str]=None
    emailto_send_id:Optional[str]=None


class UpdateOrderSchema(BaseModel):
    order_id:str
    customer_id:str
    product_id:str
    activated:Optional[bool]=None
    additional_price:Optional[int]=None
    unit_price:Optional[float]=None
    distributor_id:Optional[str]=None
    discount_id:Optional[str]=None
    quantity:Optional[int]=None
    additional_discount:Optional[str]=None
    delivery_info:Optional[DeliveryInfo]=None
    status_info:Optional[List[StatusInfo]]=None
    logistic_info:Optional[LogisticsInfo]=None
    vendor_commision:Optional[str]=None
    emailto_send_id:Optional[str]=None

class RecoverOrderSchema(BaseModel):
    order_id:str
    customer_id:str



class OrderFilterSchema(BaseModel):
    payment_status:Optional[Union[str,PaymentStatus,None]]=None
    invoice_status:Optional[Union[str,InvoiceStatus,None]]=None
    purchase_type:Optional[Union[str,PurchaseTypes,None]]=None
    renewal_type:Optional[Union[str,RenewalTypes,None]]=None
    activation_status:Optional[Union[bool,None]]=None
    distributor_type:Optional[Union[str,DistributorType,None]]=None
    distributor_id:Optional[str]=None
    revenue_type:Optional[Union[str,OrderFilterRevenueEnum,None]]=None
    date_filter:Optional[OrderDateFilterTypDict]=OrderDateFilterTypDict()