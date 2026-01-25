import pandas as pd
import json
from icecream import ic


def extract_excel_data(excel_file,headings_mapper:dict):
    ex_data=pd.read_excel(excel_file)
    df=pd.DataFrame(data=ex_data)
    converted_data=df.to_dict('dict')
    print(converted_data)
    if len(headings_mapper)!=len(converted_data):
        print("Insufficient headings")
        return False
    
    final_data=[]
    is_breaked=False
    for key,value in converted_data.items():
        index=0
        for j in value.values():
            mapper_key=headings_mapper.get(key)
            if mapper_key is None:
                print("Mistmatched Heading")
                is_breaked=True
                break

            mapper_value=j
            if (mapper_key == "mobile_number" or mapper_key == "gst_number") and mapper_value is not None:
                mapper_value = str(int(mapper_value))
            if isinstance(j,str) and (j[0]=='{' and j[-1]=='}'):
                mapper_value=eval(j)
                
            try:
                final_data[index]
                final_data[index][mapper_key]=mapper_value
            except:
                final_data.insert(index,{mapper_key:mapper_value})

            index+=1
        index=0
    ic(final_data)
    return [] if is_breaked else final_data


if __name__=="__main__":
    ...
    # excel_file='TibosAccountsDataFormat.xlsx'
    # headings_mapper={
    #     'company_name': 'name',
    #     "mobile_number": 'mobile_number',
    #     "email": 'email',
    #     "gst_number": 'gst_number',
    #     "no_of_employee": 'no_of_employee',
    #     "website_url": 'website_url',
    #     "industry": 'industry',
    #     "sector": 'sector',
    #     "address": 'address',
    #     "owner": 'owner',
    #     "tenant_id": 'tenant_id'   
    # }

    # print(extract_excel_data(excel_file=excel_file,headings_mapper=headings_mapper))
