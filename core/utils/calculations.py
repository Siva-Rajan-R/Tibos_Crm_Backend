from .discount_validator import validate_discount,parse_discount
from datetime import date,datetime
from typing import Union
from icecream import ic


def get_remaining_days(from_date:Union[str,date],to_date:Union[str,date]):
    formated_from_date=from_date
    formated_to_date=to_date    
    ic(formated_from_date,formated_to_date)
    if isinstance(from_date,str):
        formated_from_date=datetime.strptime(from_date, "%Y-%m-%d").date()
    if isinstance(to_date,str):
        formated_to_date=datetime.strptime(to_date, "%Y-%m-%d").date()

    remaining_days=formated_from_date-formated_to_date

    return remaining_days.days

print(get_remaining_days("2025-01-01","2025-01-10"))


def get_distributor_amount(product_price:int,qty:int,distri_discount:str,addti_discount:str):
    total_price=product_price*qty
    distri_price=total_price-parse_discount(discount=distri_discount,total=total_price)
    total_price=distri_price

    additi_price=total_price-parse_discount(discount=addti_discount,total=product_price)
    total_price=additi_price

    return total_price
