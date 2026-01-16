from typing import TypedDict
from datetime import date
from ..enums.pg_enums import ShippingMethods
from ..enums.payment_enums import PaymentTermsEnum

class DeliveryInfo(TypedDict):
    requested_date:date
    delivery_date:date
    shipping_method:ShippingMethods
    payment_terms:PaymentTermsEnum