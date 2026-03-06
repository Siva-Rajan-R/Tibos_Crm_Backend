from icecream import ic
import json


def account_data_converter(data:dict):
    ic(data)
    temp_data=dict(data)
    for key,value in temp_data['address'].items():
        temp_data[key]=value
    temp_data['emails']=', '.join(temp_data['emails'])
    temp_data['customer_created_at']=str(temp_data['customer_created_at'])
    ic("final_temp_data => ",temp_data)
    return temp_data

def contact_data_converter(data:dict):
    ic(data)
    temp_data=dict(data)
    temp_data['contact_created_at']=str(temp_data['contact_created_at'])
    return temp_data

def product_data_converter(data:dict):
    ic(data)
    temp_data=dict(data)
    temp_data['product_created_at']=str(temp_data['product_created_at'])
    return temp_data

def distributor_data_converter(data:dict):
    ic(data)
    temp_data=dict(data)
    ic(temp_data['discounts'])

    temp_data['created_at']=str(temp_data['created_at'])
    return temp_data

def order_data_converter(data:dict):
    ic(data)
    temp_data=dict(data)
    for di_key,di_val in data['delivery_info'].items():
        temp_data[di_key]=di_val
    ic(data['status_info'])

    for li_key,li_val in data['logistic_info'].items():
        temp_data[li_key]=li_val
    
    status_info={}
    for sts_info in data['status_info']:
        status_info[sts_info['invoice_number']]=sts_info
    
    temp_data['last_order_date']=str(temp_data['last_order_date'])
    temp_data['order_created_at']=str(temp_data['order_created_at'])
    temp_data['last_order_expiry_date']=str(temp_data['last_order_expiry_date'])
    status_info['status_info']=status_info

    del temp_data['delivery_info']
    del temp_data['logistic_info']
    ic(temp_data)
    return temp_data


DATA_CONVERTER_MAPPER={
    'ACCOUNTS':account_data_converter,
    'CONTACTS':contact_data_converter,
    'PRODUCTS':product_data_converter,
    'DISTRIBUTORS':distributor_data_converter,
    "ORDERS":order_data_converter
}


def convert_data_to_excel_format(mapper:dict,data:list,converter_name:str):
    final_ans=[]
    temp_dict={}
    ic(data)
    for i in data:
        fined_data=DATA_CONVERTER_MAPPER[converter_name.upper()](data=i)
        for key,val in mapper.items():
            temp_dict[val]=fined_data[key]
        final_ans.append(temp_dict)
        temp_dict={}

    return final_ans