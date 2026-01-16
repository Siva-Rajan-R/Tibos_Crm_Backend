from typing import TypedDict,Optional


class CustomerAddressTypDict(TypedDict):
    address:str
    pincode:str
    city:str
    state:str