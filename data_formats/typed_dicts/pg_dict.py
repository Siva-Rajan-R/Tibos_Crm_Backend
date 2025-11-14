from typing import TypedDict
from datetime import date
from data_formats.enums.pg_enums import ShippingMethods

class DeliveryInfo(TypedDict):
    requested_date:date
    delivery_date:date
    shipping_method:ShippingMethods
    payment_terms:str
    freight_terms:str
