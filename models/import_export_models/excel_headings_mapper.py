PRODUCTS_MAPPER={
    'product_name':'name',
    'product_description':'description',
    'qty':'available_qty',
    'product_type':'product_type',
    'product_price':'price',
    'part_number':'part_number'
}

# ACCOUNTS_MAPPER={
#     'company_name': 'name',
#     "mobile_number": 'mobile_number',
#     "email": 'email',
#     "gst_number": 'gst_number',
#     "no_of_employee": 'no_of_employee',
#     "website_url": 'website_url',
#     "industry": 'industry',
#     "sector": 'sector',
#     "address": 'address',
#     "city":"city",
#     "state":"state",
#     "pincode":"pincode",
#     "owner": 'owner',
#     "tenant_id": 'tenant_id'   
# }

ACCOUNTS_MAPPER={
    "company_name": "name",
    "mobile_number": 'mobile_number',
    "email": 'email',
    "gst_number": 'gst_number',
    "no_of_employee": 'no_of_employee',
    "website_url": 'website_url',
    "industry": 'industry',
    "sector": 'sector',
    "address": 'address',
    "owner": 'owner',
    "tenant_id": 'tenant_id'   
}

CONTACTS_MAPPER={
    'account_id':'customer_id',
    'name':'name',
    'mobile_number':'mobile_number',
    'email':'email'
}

DISTRI_MAPPER={
    'name':'name',
    'discount':'discount'
}

ORDERS_MAPPER={
    'customer_id':'customer_id',
    'product_id':'product_id',
    'distributor_id':'distributor_id',
    'quantity':'quantity',
    'additional_discount':'discount',
    'per_unit_price':'unit_price',
    'vendor_commision':'vendor_commision',
    'bill_to':'bill_to',
    'order_cnf_date':'requested_date',
    'renewal_type':'renewal_type',
    'purchase_type':'purchase_type',
    'activation_date':'delivery_date',
    'payment_terms':'payment_terms',
    'shipping_method':'shipping_method',
    'payment_status':'payment_status',
    'invoice_status':'invoice_status',
    'invoice_number':'invoice_number',
    'invoice_date':'invoice_date',
    'product_rebate_type':'distributor_type'
}
