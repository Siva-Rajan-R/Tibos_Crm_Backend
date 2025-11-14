# import json

# email="siva"

# print(email.replace('@','_').replace('.','_'))

# at="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJkYXRhIjoiZ0FBQUFBQnBCNlBTU3doRC1DZEJIOENMWl9pWlZJZG9NM1B0MV9jbGdFaGZTNS13V1lYWUNZdkEydEVqemNJMDJmX0wxTmtEYzZiSzV0WWJ4Qzc1OGI1VjN1cXlSSXJXUXJXazhVSEZCeGV1d1lvX1dfcUxjRDhKU2ZybDJQbzJ0WEJmNFc4SGZQN0VtRW9oNkdnWWZhN0hvVFQ4VU1KQXRBPT0iLCJleHAiOjE3NjI3MTMxNzAsImlzcyI6IkRlQi1BdXRoIn0._IIxcZZ6AjE14tF6YJ5ooUeggKThqxce7yF8bFAJQqQ"
# rt="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJkYXRhIjoiZ0FBQUFBQnBCNTcydnZWM0RGTVYybnVRUWZpWlgxemNlWE9UTWdUUTlQMkVQbW9LcUl3RFBIbHh0Q2l1T2w0TDFVVlVzZU9RM3p5UGsyV2h5eWZfbEROR0NhV2RCZ0R5N0hMWjhSa2F2VEZXbnFZSUFJaWF6aGpPOVhtVUxKeWg2cDdNdUtVYUhxdFU5N2NPdU1LNDRPSDN6TWtfOE9zdGl3PT0iLCJleHAiOjE3NjI3MTE5MjYsImlzcyI6IkRlQi1BdXRoIn0.Q-hbhazkFxAdETbF1cqIcMmEonDsj05Wdgtg938XhGE"


from abc import ABC,abstractmethod

class BaseCrud(ABC):
    @abstractmethod
    async def add(self,*args,**kwargs):
        ...
    
    @abstractmethod
    async def update(self,*args,**kwargs):
        ...
    
    @abstractmethod
    async def delete(self,*args,**kwargs):
        ...
    
    @abstractmethod
    async def get(self,*args,**kwargs):
        ...
    
    @abstractmethod
    async def get_by_id(self,*args,**kwargs):
        ...

class Test(BaseCrud):
    async def add(self):
        print("hi add")


obj = Test()
obj.add()