from .models.order import Orders,OrdersPaymentInvoiceInfo
from .models.product import Products
from .models.distributor import Distributors
from sqlalchemy import func,case,cast,Date,Numeric,select
from core.data_formats.enums.order_enums import PurchaseTypes
from core.utils.calculations import get_customer_addon_price,get_distri_addon_price,get_customer_price,get_distributor_price,get_profit_loss_price,get_remaining_days,get_total_price
from datetime import timedelta,datetime
from core.constants import DEFAULT_ADDON_YEAR
from sqlalchemy.orm import aliased

PrevOrder = aliased(Orders)

customer_tot_price=func.coalesce(Orders.unit_price*Orders.quantity,0)

total_paid_amount = func.coalesce(
    func.sum(OrdersPaymentInvoiceInfo.paid_amount), 0
)

distributor_tot_price=func.coalesce(Products.price*Orders.quantity,0)


distri_discount=(select(Distributors.discounts[Orders.discount_id]).where(Distributors.id==Orders.distributor_id).correlate_except(Distributors)).scalar_subquery()
last_order_delivery_date = (
    select(
        cast(PrevOrder.delivery_info['delivery_date'].astext, Date)
    )
    .where(
        PrevOrder.customer_id == Orders.customer_id,
        PrevOrder.product_id == Orders.product_id,
        PrevOrder.is_deleted == False,
        PrevOrder.logistic_info['purchase_type'].astext != PurchaseTypes.EXISTING_ADD_ON.value
    )
    .order_by(
        cast(PrevOrder.delivery_info['delivery_date'].astext, Date).desc()
    )
    .limit(1)
    .scalar_subquery()
)

cur_order_delivery_date = cast(
    Orders.delivery_info['delivery_date'].astext,
    Date
)

expiry_date = last_order_delivery_date + func.make_interval(
    0,  # years
    0,  # months
    0,  # weeks
    DEFAULT_ADDON_YEAR + 1,  # days
    0,  # hours
    0,  # minutes
    0   # seconds
)


remaining_days = func.greatest(
    func.extract(
        "day",
        expiry_date - cur_order_delivery_date
    ),
    0
)

distri_disc_price=case(
    (
        distri_discount['discount'].astext.ilike("%\%%"),
        func.round(   
            distributor_tot_price
            -
            ((cast(func.coalesce(func.replace(distri_discount['discount'].astext,'%',''),'0'),Numeric)/100)
            *
            distributor_tot_price)
        )
    ),
    else_=(func.round(distributor_tot_price-cast(func.coalesce(distri_discount['discount'].astext,'0'),Numeric)))
)

distri_additi_price=case(
    (
        Orders.additional_discount.ilike("%\%%"),
        func.round(
            distributor_tot_price
            -
            ((cast(func.coalesce(func.replace(Orders.additional_discount,'%',''),'0'),Numeric)/100)
            *
            distributor_tot_price)
        
        )
    ),
    else_=(func.round(distri_disc_price-cast(
        func.coalesce(
            func.nullif(Orders.additional_discount, ''),
            '0'
        ),
        Numeric
    )))
)



distri_final_price=case(
    (
        Orders.logistic_info['purchase_type'].astext==PurchaseTypes.EXISTING_ADD_ON.value,
        func.round((((distri_additi_price+distri_disc_price)-distributor_tot_price)/DEFAULT_ADDON_YEAR)
        *
        remaining_days
        )
    ),
    else_=(func.round(((distri_additi_price+distri_disc_price)-distributor_tot_price)))

)


customer_amount_with_gst=customer_tot_price*1.18
pending_amount=func.round(customer_amount_with_gst)-func.round(total_paid_amount)

customer_final_price=case(
    (
        Orders.logistic_info['purchase_type'].astext==PurchaseTypes.EXISTING_ADD_ON.value,
        func.round(
           (Orders.unit_price/DEFAULT_ADDON_YEAR)
            *
            remaining_days
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
