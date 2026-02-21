from icecream import ic


def account_data_converter(data:dict):
    ic(data)
    temp_data=dict(data)
    for key,value in temp_data['address'].items():
        temp_data[key]=value
    temp_data['emails']=', '.join(temp_data['emails'])
    ic("final_temp_data => ",temp_data)
    return temp_data


def contact_data_converter(data:dict):
    ic(data)
    temp_data=dict(data)
    return temp_data

def product_data_converter(data:dict):
    ic(data)
    temp_data=dict(data)
    return temp_data

def product_data_converter(data:dict):
    ic(data)
    temp_data=dict(data)
    return temp_data


def distributor_data_converter(data:dict):
    ic(data)
    temp_data=dict(data)
    return temp_data

def order_data_converter(data:dict):
    ic(data)
    temp_data=dict(data)
    for di_key,di_val in data['delivery_info'].items():
        temp_data[di_key]=di_val

    for sti_key,sti_val in data['status_info'].items():
        temp_data[sti_key]=sti_val

    for li_key,li_val in data['logistic_info'].items():
        temp_data[li_key]=li_val
    
    if 'invoice_date' not in temp_data:
        temp_data['invoice_date']=''
    if 'invoice_number' not in temp_data:
        temp_data['invoice_number']=''

    del temp_data['delivery_info']
    del temp_data['status_info']
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
    for i in data:
        fined_data=DATA_CONVERTER_MAPPER[converter_name.upper()](data=i)
        for key,val in mapper.items():
            ic(key,val)
            temp_dict[val]=fined_data[key]
        final_ans.append(temp_dict)
        temp_dict={}

    return final_ans