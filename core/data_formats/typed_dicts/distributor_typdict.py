from typing import TypedDict,Optional,Union
from core.data_formats.enums.order_enums import DistributorType
from datetime import date

class DistributorDiscountsTypDict(TypedDict):
    discount:str
    minimum_thershold:int
    rebate_type:DistributorType

class DistributorPaymentInfosTypDict(TypedDict):
    invoice_number:Optional[Union[None,str]]=None
    invoice_value:Optional[Union[int,None]]=None
    paid_amount:Optional[Union[None,int]]=None
    paid_date:Optional[Union[None,date]]=None