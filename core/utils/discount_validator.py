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


def parse_discount(discount, total):
    print("discount", discount, "total", total)

    if not discount:
        ic("parsed discount value =>",0)
        return 0

    discount_str = str(discount).strip()

    if discount_str.endswith("%"):
        percent = float(discount_str.replace("%", ""))
        ic("parsed discount value =>",total * (percent / 100))
        return total * (percent / 100)

    try:
        ic("parsed discount value =>",discount)
        return float(discount)
    
    except (ValueError, TypeError):
        ic("parsed discount value =>",0)
        return 0
