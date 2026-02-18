from typing import TypedDict,Optional,Union


class CustomerAddressTypDict(TypedDict):
    address:str
    pincode:str
    city:str
    state:str