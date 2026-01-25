import pandas as pd


data={'company_name': ["Debuggers"],
"mobile_number": ["1234567890"],
"email": ["debuggers@gmail.com"],
"gst_number": ["12345"],
"no_of_employee": [10],
"website_url": ["https:///debuggers.com"],
"industry": ["Agriculture"],
"sector": ["PRIVATE"],
"address": [{
    "city": "MADURAI",
    "state": "TAMILNADU",
    "address": "vasugi nagar, murugan kovil",
    "pincode": "625022"
}],
"owner": ["Siva Rajan"],
"tenant_id": ["tenant_12345"]
}
df=pd.DataFrame(data)
df.to_excel("TibosAccountsDataFormat.xlsx",index=False)
