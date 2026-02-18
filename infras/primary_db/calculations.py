from .models.order import Orders
from .models.product import Products
from .models.distributor import Distributors
from sqlalchemy import func,case,cast,Date,Numeric
from core.data_formats.enums.order_enums import PurchaseTypes
from core.utils.calculations import get_customer_addon_price,get_distri_addon_price,get_customer_price,get_distributor_price,get_profit_loss_price,get_remaining_days,get_total_price
from datetime import timedelta,datetime
from core.constants import DEFAULT_ADDON_YEAR

customer_tot_price=func.coalesce(Orders.unit_price*Orders.quantity,0)
distributor_tot_price=func.coalesce(Products.price*Orders.quantity,0)

distri_disc_price=case(
    (
        Distributors.discount.ilike("%\%%"),
        func.round(   
            distributor_tot_price
            -
            ((cast(func.coalesce(func.replace(Distributors.discount,'%',''),'0'),Numeric)/100)
            *
            distributor_tot_price)
        )
    ),
    else_=(func.round(distributor_tot_price-cast(func.coalesce(Distributors.discount,'0'),Numeric)))
)

distri_additi_price=case(
    (
        Orders.additional_discount.ilike("%\%%"),
        func.round(
            distri_disc_price
            -
            ((cast(func.coalesce(func.replace(Orders.additional_discount,'%',''),'0'),Numeric)/100)
            *
            distri_disc_price)
        
        )
    ),
    else_=(func.round(distri_disc_price-cast(func.coalesce(Orders.additional_discount,'0'),Numeric)))
)



distri_final_price=case(
    (
        Orders.logistic_info['purchase_type'].astext==PurchaseTypes.EXISTING_ADD_ON.value,
        func.round((distri_additi_price/DEFAULT_ADDON_YEAR)
        *
        (cast(Orders.logistic_info['last_ord_expiry_date'].astext,Date)-cast(Orders.delivery_info['delivery_date'].astext,Date)))
    ),
    else_=(func.round(distri_additi_price))

)


customer_final_price=case(
    (
        Orders.logistic_info['purchase_type'].astext==PurchaseTypes.EXISTING_ADD_ON.value,
        func.round(
           (Orders.unit_price/DEFAULT_ADDON_YEAR)
            *
            (cast(Orders.logistic_info['last_ord_expiry_date'].astext,Date)-cast(Orders.delivery_info['delivery_date'].astext,Date))
            *
            Orders.quantity 
        )
    ),
    else_=(func.round(customer_tot_price))

)

vendor_disc_price=case(
    (
        Orders.vendor_commision.ilike("%\%%"),
        func.round(
            
            (
                (cast(func.coalesce(func.replace(Orders.vendor_commision,'%',''),'0'),Numeric)/100)
                *
                Orders.unit_price
            )
            *
            Orders.quantity
            
        )
    ),
    else_=(func.round(cast(func.coalesce(Orders.vendor_commision,'0'),Numeric)*Orders.quantity))
)


profit_loss_price=func.round(customer_final_price-vendor_disc_price-distri_final_price)
