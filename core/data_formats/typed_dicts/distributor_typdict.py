from typing import TypedDict
from core.data_formats.enums.order_enums import DistributorType

class DistributorDiscountsTypDict(TypedDict):
    discount:str
    minimum_thershold:int
    rebate_type:DistributorType