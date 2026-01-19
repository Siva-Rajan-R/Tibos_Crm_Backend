from typing import TypedDict,Optional
from ..enums.common_enums import IndianStatesEnum


class CustomerAddressTypDict(TypedDict):
    address:str
    pincode:str
    city:str
    state:IndianStatesEnum