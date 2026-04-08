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
    last_order_id:Optional[str]=None
    quantity:int
    activated:bool
    additional_discount:str
    additional_price:Optional[float]=None
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
    last_order_id:Optional[str]=None
    activated:Optional[bool]=None
    additional_price:Optional[float]=None
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


class AddSearchField(BaseModel):
    ui_id:str
    id:str
    distributor_name:str
    distributor_ui_id:str
    product_type:str
    product_name:str
    product_ui_id:str
    customer_email:str
    customer_name:str
    customer_ui_id:str
    product_id:str
    distributor_id:str
    customer_id:str

class UpdateSearchField(BaseModel):
    distributor_name:Optional[str]=None
    distributor_ui_id:Optional[str]=None
    product_type:Optional[str]=None
    product_name:Optional[str]=None
    product_ui_id:Optional[str]=None
    customer_email:Optional[str]=None
    customer_name:Optional[str]=None
    customer_ui_id:Optional[str]=None
    product_id:Optional[str]=None
    distributor_id:Optional[str]=None
    customer_id:Optional[str]=None

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
    customer_id:Optional[str]=None
    distributor_id:Optional[str]=None
    product_id:Optional[str]=None
    owner_name:Optional[str]=None
    revenue_type:Optional[Union[str,OrderFilterRevenueEnum,None]]=None
    date_filter:Optional[OrderDateFilterTypDict]=OrderDateFilterTypDict()


class OrderBulkDeleteSchema(BaseModel):
    order_ids:List[str]


class AddCartOrderProductSchema(BaseModel):
    product_id:str
    discount_id:str
    additional_price:float
    additional_discount:str
    quantity:int
    unit_price:float

class AddCartOrderSchema(BaseModel):
    customer_id:str
    distributor_id:str
    activated:bool
    delivery_info:DeliveryInfo
    status_info:List[StatusInfo]
    logistic_info:LogisticsInfo
    products:List[AddCartOrderProductSchema]
    vendor_commision:Optional[str]=None



class UpdateCartOrderProductSchema(BaseModel):
    order_id:str
    product_id:str
    discount_id:str
    additional_price:float
    additional_discount:str
    quantity:int
    unit_price:float

class UpdateCartOrderSchema(BaseModel):
    order_id:str
    customer_id:str
    distributor_id:str
    activated:bool
    delivery_info:DeliveryInfo
    status_info:List[StatusInfo]
    logistic_info:LogisticsInfo
    products:List[UpdateCartOrderProductSchema]
    vendor_commision:Optional[str]=None