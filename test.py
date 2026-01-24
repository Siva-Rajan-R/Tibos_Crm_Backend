import pandas as pd

data={'name':['siva'],'age':[18]}
ex_data=pd.read_csv('tibos.csv',encoding="latin1")
df=pd.DataFrame(data=ex_data)
# df.to_excel('output.xlsx',index=False)
print(df.to_dict())