from typing import TypedDict,Optional,NotRequired,List,Union
from datetime import date
from ..enums.order_enums import ShippingMethods,PaymentStatus,PurchaseTypes,InvoiceStatus,DistributorType,PaymentTermsEnum,RenewalTypes
from ..enums.product_enums import ProductTypes
from ..enums.order_enums import OrderFilterDateByEnum

class DeliveryInfo(TypedDict):
    requested_date:date
    delivery_date:date
    shipping_method:ShippingMethods
    payment_terms:PaymentTermsEnum

class StatusInfo(TypedDict):
    payment_status:NotRequired[Union[str,None,PaymentStatus]]=None
    invoice_status:Union[str,InvoiceStatus]
    invoice_number:NotRequired[Union[str,None]]=None
    invoice_date:NotRequired[Union[date,None]]=None
    paid_amount:NotRequired[Union[float,None]]=None

class LogisticsInfo(TypedDict):
    purchase_type:Union[str,PurchaseTypes]
    last_ord_expiry_date:NotRequired[Union[date,None]]
    last_order_id:NotRequired[Union[str,None]]
    renewal_type:Union[str,RenewalTypes]
    bill_to:NotRequired[str]
    distributor_type:Union[str,DistributorType]

class OrderDateFilterTypDict(TypedDict):
    from_date:date
    to_date:date
    by:OrderFilterDateByEnum