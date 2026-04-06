from typing import TypedDict,Optional,Union
from core.data_formats.enums.order_enums import DistributorType
from datetime import date

class DistributorDiscountsTypDict(TypedDict):
    discount:str
    minimum_thershold:float
    rebate_type:str

class DistributorPaymentInfosTypDict(TypedDict):
    partner_invoice_no:Union[str,None]
    partner_invoice_date: Union[date,None]
    per_qty_bill: Union[float,None]
    total_billed: Union[float,None]
    paid_date: Union[date,None]
    paid_amount: Union[float,None]
    month: Optional[str]=""