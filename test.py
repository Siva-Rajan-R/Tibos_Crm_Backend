# # import requests


# # print(requests.post("https://countriesnow.space/api/v0.1/countries/state/cities",json={'state':'Tamil Nadu','city':'Madurai'}).json())

# import pandas as pd

# ACCOUNTS_MAPPER={
#     "company_name": "name",
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

# FILE_NAME='TibosAccountsDataFormat.xlsx'

# # df=pd.DataFrame(ORDERS_MAPPER)
# # df.to_excel(FILE_NAME,index=False)

# # ex_data=pd.read_excel(FILE_NAME)
# # df=pd.DataFrame(data=ex_data)
# # converted_data=df.to_dict('records')
# # print(converted_data)


# import pandas as pd
# import json
# from icecream import ic


# def extract_excel_data(excel_file,headings_mapper:dict):
#     ic(headings_mapper)
#     ex_data=pd.read_excel(excel_file)
#     df=pd.DataFrame(data=ex_data)
#     converted_data=df.to_dict('records')
        
#     if len(headings_mapper.keys())!=len(converted_data[0].keys()):
#         print("Insufficient headings")
#         return False
    
#     final_data=[]
#     temp_dict={}
#     is_breaked=False
#     for data in converted_data:
#         for key,val in data.items():
#             try:
#                 key_toadd=headings_mapper[key]
#                 if key_toadd=="mobile_number" or key_toadd=="gst_number":
#                     val=str(val).strip().replace(" ","")
                
#                 if key_toadd=="mobile_number" and len(val)>10:
#                     temp_dict.clear()
#                     break

#                 if isinstance(val,str) and val[0]=="{" and val[-1]=="}":
#                     val=eval(val)

#                 temp_dict[key_toadd]=val
#                 ic(temp_dict)

#             except Exception as e:
#                 ic("Ur Exceptions =>",e)
#                 is_breaked=True
#                 break

#         if is_breaked:
#             break

#         if len(temp_dict)>0:
#             final_data.append(temp_dict)
#         temp_dict={}
    
#     return final_data if not is_breaked else None


# print(extract_excel_data(excel_file=FILE_NAME,headings_mapper=ACCOUNTS_MAPPER))




import requests

TENANT_ID = "5306f651-8fb6-47ee-8b65-2685aadbc3c0"
CLIENT_ID = "27f272ed-19e9-4460-a0c0-13d40b3855c8"
CLIENT_SECRET = "Tij8Q~mb85YqaqiPKvyyQiy4QjKRLbqLbeO0jawH"

def get_token():
    url = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"
    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "scope": "https://graph.microsoft.com/.default",
        "grant_type": "client_credentials",
    }
    res = requests.post(url, data=data,headers={"Content-Type": "application/x-www-form-urlencoded"})
    print(res.text)
    res.raise_for_status()
    return res.json()["access_token"]


ACCESS_TOKEN = get_token()

url = "https://graph.microsoft.com/v1.0/users/crm@tibos.in/sendMail"

headers = {
    "Authorization": f"Bearer {ACCESS_TOKEN}",
    "Content-Type": "application/json",
}

payload = {
    "message": {
        "subject": "Graph API test",
        "body": {
            "contentType": "HTML",
            "content": "<h2>Email sent using Microsoft Graph API</h2>"
        },
        "toRecipients": [
            {"emailAddress": {"address": "siva@tibos.in"}}
        ]
    },
    "saveToSentItems": True
}

res = requests.post(url, headers=headers, json=payload)
print(res.status_code)
print(res.text)

