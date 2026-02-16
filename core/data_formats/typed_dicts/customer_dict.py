from typing import TypedDict,Optional,Union
from ..enums.common_enums import IndianStatesEnum


class CustomerAddressTypDict(TypedDict):
    address:str
    pincode:str
    city:str
    state:str