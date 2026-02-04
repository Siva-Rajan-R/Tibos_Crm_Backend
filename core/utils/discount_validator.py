from typing import Optional, Union
from icecream import ic


def validate_discount(value:str)->Optional[Union[float,str]]:
    ic("Discount value : ",value)
    is_discount=None
    try:
        print('hello')
        is_discount=float(value)
    except Exception as e:
        ic(e)
        if value[-1]=="%":
            try:
                sliced_value=value[0:-1]
                float(sliced_value)
                ic(value,sliced_value)
                is_discount=float(sliced_value)
            except Exception as e:
                is_discount=None
        else:
            is_discount=None

    return is_discount