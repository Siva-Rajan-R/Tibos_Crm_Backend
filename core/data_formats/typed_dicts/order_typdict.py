from typing import TypedDict,Optional,NotRequired
from datetime import date
from ..enums.order_enums import ShippingMethods,PaymentStatus,PurchaseTypes,InvoiceStatus,DistributorType,PaymentTermsEnum,RenewalTypes
from ..enums.product_enums import ProductTypes

class DeliveryInfo(TypedDict):
    requested_date:date
    delivery_date:date
    shipping_method:ShippingMethods
    payment_terms:PaymentTermsEnum

class StatusInfo(TypedDict):
    payment_status:PaymentStatus
    invoice_status:InvoiceStatus
    invoice_number:NotRequired[str]
    invoice_date:NotRequired[date]

class LogisticsInfo(TypedDict):
    purchase_type:PurchaseTypes
    last_ord_expiry_date:NotRequired[date]
    renewal_type:RenewalTypes
    bill_to:NotRequired[str]
    distributor_type:DistributorType