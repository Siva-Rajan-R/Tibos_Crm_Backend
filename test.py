# import requests


# print(requests.post("https://countriesnow.space/api/v0.1/countries/state/cities",json={'state':'Tamil Nadu','city':'Madurai'}).json())

import pandas as pd

DISTRI_MAPPER={
    'name':[],
    'discount':[]
}
FILE_NAME='TibosDistriDataFormat.xlsx'

# df=pd.DataFrame(DISTRI_MAPPER)
# df.to_excel(FILE_NAME,index=False)

ex_data=pd.read_excel(FILE_NAME)
df=pd.DataFrame(data=ex_data)
converted_data=df.to_dict('dict')
print(converted_data)