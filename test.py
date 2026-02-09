# import requests


# print(requests.post("https://countriesnow.space/api/v0.1/countries/state/cities",json={'state':'Tamil Nadu','city':'Madurai'}).json())

import pandas as pd

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

FILE_NAME='TibosAccountsDataFormat.xlsx'

# df=pd.DataFrame(ORDERS_MAPPER)
# df.to_excel(FILE_NAME,index=False)

# ex_data=pd.read_excel(FILE_NAME)
# df=pd.DataFrame(data=ex_data)
# converted_data=df.to_dict('records')
# print(converted_data)


import pandas as pd
import json
from icecream import ic


def extract_excel_data(excel_file,headings_mapper:dict):
    ic(headings_mapper)
    ex_data=pd.read_excel(excel_file)
    df=pd.DataFrame(data=ex_data)
    converted_data=df.to_dict('records')
        
    if len(headings_mapper.keys())!=len(converted_data[0].keys()):
        print("Insufficient headings")
        return False
    
    final_data=[]
    temp_dict={}
    is_breaked=False
    for data in converted_data:
        for key,val in data.items():
            try:
                key_toadd=headings_mapper[key]
                if key_toadd=="mobile_number" or key_toadd=="gst_number":
                    val=str(val).strip().replace(" ","")
                
                if key_toadd=="mobile_number" and len(val)>10:
                    temp_dict.clear()
                    break

                if isinstance(val,str) and val[0]=="{" and val[-1]=="}":
                    val=eval(val)

                temp_dict[key_toadd]=val
                ic(temp_dict)

            except Exception as e:
                ic("Ur Exceptions =>",e)
                is_breaked=True
                break

        if is_breaked:
            break

        if len(temp_dict)>0:
            final_data.append(temp_dict)
        temp_dict={}
    
    return final_data if not is_breaked else None


print(extract_excel_data(excel_file=FILE_NAME,headings_mapper=ACCOUNTS_MAPPER))



