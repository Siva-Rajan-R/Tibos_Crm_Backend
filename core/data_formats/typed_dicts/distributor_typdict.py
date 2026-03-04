from typing import TypedDict
from core.data_formats.enums.order_enums import DistributorType
from datetime import date

class DistributorDiscountsTypDict(TypedDict):
    discount:str
    minimum_thershold:int
    rebate_type:DistributorType

class DistributorPaymentInfosTypDict(TypedDict):
    invoice_number:str
    invoice_value:int
    paid_amount:int
    paid_date:date