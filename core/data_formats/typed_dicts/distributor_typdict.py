from typing import TypedDict,Optional,Union
from core.data_formats.enums.order_enums import DistributorType
from datetime import date

class DistributorDiscountsTypDict(TypedDict):
    discount:str
    minimum_thershold:float
    rebate_type:str

class DistributorPaymentInfosTypDict(TypedDict):
    invoice_number:Optional[Union[None,str]]=None
    invoice_value:Optional[Union[float,None]]=None
    paid_amount:Optional[Union[None,float]]=None
    paid_date:Optional[Union[None,date]]=None