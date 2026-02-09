# import requests


# print(requests.post("https://countriesnow.space/api/v0.1/countries/state/cities",json={'state':'Tamil Nadu','city':'Madurai'}).json())

import pandas as pd

ORDERS_MAPPER={
    'customer_id':[],
    'product_id':[],
    'distributor_id':[],
    'quantity':[],
    'additional_discount':[],
    'per_unit_price':[],
    'vendor_commision':[],
    'bill_to':[],
    'order_cnf_date':[],
    'purchase_type':[],
    'activation_date':[],
    'payment_terms':[],
    'shipping_method':[],
    'payment_status':[],
    'invoice_status':[],
    'invoice_number':[],
    'invoice_date':[],
    'product_rebate_type':[]
}

FILE_NAME='TibosOrderDataFormat.xlsx'

df=pd.DataFrame(ORDERS_MAPPER)
df.to_excel(FILE_NAME,index=False)

# ex_data=pd.read_excel(FILE_NAME)
# df=pd.DataFrame(data=ex_data)
# converted_data=df.to_dict('dict')
# print(converted_data)