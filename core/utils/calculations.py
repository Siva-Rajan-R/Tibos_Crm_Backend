from .discount_validator import validate_discount,parse_discount
from datetime import date,datetime
from typing import Union
from icecream import ic
from ..constants import DEFAULT_GST,DEFAULT_ADDON_YEAR


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


def get_total_price(price:int,qty:int):
    total_price=price*qty
    return total_price

def get_distributor_price(product_price:int,qty:int,distri_discount:str,addti_discount:str):
    total_price=get_total_price(price=product_price,qty=qty)
    distri_price=total_price-parse_discount(discount=distri_discount,total=total_price)
    total_price=distri_price

    additi_price=total_price-parse_discount(discount=addti_discount,total=product_price)
    total_price=additi_price

    without_gst=total_price
    with_gst=without_gst+parse_discount(discount=DEFAULT_GST,total=without_gst)
    
    return {
        'without_gst':without_gst,
        'with_gst':with_gst
    }

def get_customer_price(customer_price:int,qty:int):
    total_price=get_total_price(price=customer_price,qty=qty)

    without_gst=total_price
    with_gst=without_gst+parse_discount(discount=DEFAULT_GST,total=without_gst)

    return {
        'without_gst':without_gst,
        'with_gst':with_gst
    }


def get_distri_addon_price(product_price:int,qty:int,expiry_date,delivery_date,distri_discount:str,addti_discount:str):
    remaining_days=get_remaining_days(from_date=expiry_date,to_date=delivery_date)
    distri_tot_amt=get_distributor_price(product_price=product_price,qty=1,distri_discount=distri_discount,addti_discount=addti_discount)
    unit_price=(distri_tot_amt/DEFAULT_ADDON_YEAR)*remaining_days
    total_price=unit_price*qty

    without_gst=total_price
    with_gst=without_gst+parse_discount(discount=DEFAULT_GST,total=without_gst)

    return {
        'without_gst':without_gst,
        'with_gst':with_gst,
        'unit_price':unit_price
    }


def get_customer_addon_price(customer_price:int,qty:int,expiry_date,delivery_date):
    remaining_days=get_remaining_days(from_date=expiry_date,to_date=delivery_date)
    unit_price=(customer_price/DEFAULT_ADDON_YEAR)*remaining_days
    total_price=unit_price*qty

    without_gst=total_price
    with_gst=without_gst+parse_discount(discount=DEFAULT_GST,total=without_gst)

    return {
        'without_gst':without_gst,
        'with_gst':with_gst,
        'unit_price':unit_price
    }


def get_profit_loss_price(customer_tot_price:int,distri_tot_price:int,vendor_commision:str,qty:int):
    vendor_commi_amt=parse_discount(discount=vendor_commision,total=customer_tot_price)*qty

    total_price=(customer_tot_price-vendor_commi_amt)-distri_tot_price

    without_gst=total_price
    with_gst=without_gst+parse_discount(discount=DEFAULT_GST,total=without_gst)

    return {
        'without_gst':without_gst,
        'with_gst':with_gst
    }