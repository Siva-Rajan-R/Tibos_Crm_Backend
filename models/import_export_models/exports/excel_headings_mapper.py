from icecream import ic


PRODUCTS_MAPPER={
    'quantity': 'qty',
    'description': 'product_description',
    'name': 'product_name',
    'part_number': 'part_number',
    'price': 'product_price',
    'product_type': 'product_type'
}

ACCOUNTS_MAPPER={
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
    'website_url': 'website_url'
}


CONTACTS_MAPPER={
    'customer_id': 'account_id',
    'contact_email': 'email',
    'contact_mobile': 'mobile_number',
    'contact_name': 'name'
}


DISTRI_MAPPER={
    'name':'name',
    'discount':'discount'
}

ORDERS_MAPPER={
    'customer_id': 'customer_id',
    'product_id': 'product_id',
    'distributor_id': 'distributor_id',
    'additional_discount': 'additional_discount',
    'unit_price': 'per_unit_price',
    'vendor_commision': 'vendor_commision',
    'quantity': 'quantity',

    'distributor_type': 'product_rebate_type',
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


final_dict={}
for key,val in ORDERS_MAPPER.items():
    final_dict[val]=key
ic(final_dict)
