from icecream import ic


PRODUCTS_MAPPER={
    'ui_id':'id',
    'quantity': 'qty',
    'description': 'product_description',
    'name': 'product_name',
    'part_number': 'part_number',
    'price': 'product_price',
    'product_type': 'product_type',
    'product_created_at':'product_created_at'
}

ACCOUNTS_MAPPER={
    'ui_id':'id',
    'address': 'address',
    'city': 'city',
    'emails': 'email',
    'gst_number': 'gst_number',
    'industry': 'industry',
    'mobile_number': 'mobile_number',
    'name': 'company_name',
    'no_of_employee': 'no_of_employee',
    'owner': 'owner',
    'pincode': 'pincode',
    'sector': 'sector',
    'state': 'state',
    'tenant_id': 'tenant_id',
    'website_url': 'website_url',
    'secondary_domain':'secondary_domain',
    'customer_created_at':'customer_created_at'
}


CONTACTS_MAPPER={
    'ui_id':'id',
    'customer_id': 'account_id',
    'customer_name':'customer_name',
    'contact_email': 'email',
    'contact_mobile': 'mobile_number',
    'contact_name': 'name',
    'contact_created_at':'contact_created_at'
}


DISTRI_MAPPER={
    'ui_id':'id',
    'name':'name',
    'discount':'discount',
    'rebate_type':'rebate_type',
    'minimum_thershold':'minimum_thershold',
    'created_at':'distributor_created_at'
}

ORDERS_MAPPER={
    'ui_id':'id',
    'customer_id': 'customer_id',
    'customer_name':'customer_name',
    'product_id': 'product_id',
    'product_name':'product_name',
    'distributor_id': 'distributor_id',
    'distributor_name':'distributor_name',
    'discount_id':'discount_id',
    'distributor_discount':'distributor_discount',
    'additional_discount': 'additional_discount',
    'unit_price': 'per_unit_price',
    'vendor_commision': 'vendor_commision',
    'quantity': 'quantity',
    'profit_loss':'revenue',
    'distributor_total_price':'list_distributor_price',
    'distributor_price':'net_distributor_price',
    'customer_price':'customer_price',
    'vendor_total_price':'vendor_total_price',
    'distributor_type': 'product_rebate_type',
    'last_order_date':'last_order_activation_date',
    'last_order_expiry_date':'last_order_expiry_date',
    'order_created_at':'order_created_at',

    'invoice_date': 'invoice_date',
    'invoice_number': 'invoice_number',
    'invoice_status': 'invoice_status',
    'payment_status': 'payment_status',
    'payment_terms': 'payment_terms',
    'purchase_type': 'purchase_type',
    'renewal_type': 'renewal_type',
    'requested_date': 'order_cnf_date',
    'shipping_method': 'shipping_method',
    'bill_to': 'bill_to',
    'delivery_date': 'activation_date',
}


# final_dict={}
# for key,val in ORDERS_MAPPER.items():
#     final_dict[val]=key
# ic(final_dict)
