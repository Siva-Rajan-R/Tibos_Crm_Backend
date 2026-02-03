from typing import Optional, Union
from icecream import ic


def validate_discount(value:str)->Optional[Union[float,str]]:
    ic("Discount value : ",value)
    is_discount=None
    try:
        is_discount=float(value)
    except:
        if value[-1]=="%":
            try:
                float(value[0:-1])
                is_discount=float(value)
            except:
                is_discount=None
        else:
            is_discount=None

    return is_discount