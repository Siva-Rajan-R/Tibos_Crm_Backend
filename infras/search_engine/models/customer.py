from ..main import ES
from icecream import ic
from typing import List
from elasticsearch.helpers import async_bulk,BulkIndexError
from elasticsearch import NotFoundError,ConnectionError,ConnectionTimeout
from ...primary_db.repos.customer_repo import CustomersRepo,UserRoles
from ...primary_db.main import AsyncLocalSession
from math import ceil
CUSTOMER_MODEL_NAME="customers"


class CustomerSearch:
    async def create_index(self):
        
        exists=await ES.indices.exists(index=CUSTOMER_MODEL_NAME)
        if not exists:
            res=await ES.indices.create(index=CUSTOMER_MODEL_NAME,ignore=400)
            ic(res)
        return True

        

    async def create_document(self,data:dict):
        try:
            res=await ES.index(
                index=CUSTOMER_MODEL_NAME,
                id=data['id'],
                document=data
            ) 
            ic(res)
            return res 
        except (ConnectionTimeout,ConnectionError):
            return False 
    
    async def create_bulk_doc(self,datas:List[dict]):
        def generate_actions():
            for data in datas:
                yield {
                    '_index':CUSTOMER_MODEL_NAME,
                    '_id':data['id'],
                    "_source":data
                }
        
        try:
            res = await async_bulk(ES, generate_actions(), chunk_size=1000)
            ic(res)
            return res

        except (ConnectionTimeout,ConnectionError):
            return False
        
        except BulkIndexError as e:
            print("----- BULK ERRORS -----")
            for err in e.errors[:10]:   # show first few
                print(err)
            raise
            
    
    async def update_document(self,data:dict,id:str):
        try:
            res=await ES.update(
                index=CUSTOMER_MODEL_NAME,
                id=id,
                doc=data
            )

            ic(res)

            return res

        except (ConnectionTimeout,ConnectionError):
            return False
    

    async def update_bulk_doc(self,datas:List[dict]):
        def generate_actions():
            for data in datas:
                yield {
                    '_op_type':'update',
                    '_index':CUSTOMER_MODEL_NAME,
                    '_id':data['id'],
                    "doc":data
                }
        try:
            res=await async_bulk(ES,generate_actions(),chunk_size=1000)
            ic(res)

            return res
        except (ConnectionTimeout,ConnectionError):
            return False
    
    async def delete_document(self,id:str):
        try:
            res=await ES.delete(
                index=CUSTOMER_MODEL_NAME,
                id=id
            )

            ic(res)

            return res
        
        except (ConnectionTimeout,ConnectionError):
            return False
        
        except NotFoundError:
            ic("Not FOunde Error In Elastic Search")
            pass
    
    

    async def delete_bulk_doc(self,ids:List[dict]):
        def generate_actions():
            for id in ids:
                yield {
                    'op_type':'delete',
                    '_id':id,
                    '_index':CUSTOMER_MODEL_NAME,
                }
        try:
            res=await async_bulk(ES,generate_actions(),chunk_size=1000)
            ic(res)

            return res
        
        except (ConnectionTimeout,ConnectionError):
            return False
    
    async def search_document(self,query:str,limit:int,page:int,cursor:int):
        try:
            async with AsyncLocalSession() as session:
                if not query or not query.strip():
                    ic("inside match all")
                    customers=await CustomersRepo(session=session,user_role=UserRoles.SUPER_ADMIN,cur_user_id="").get(limit=limit,in_search=[],cursor=cursor)
                    customers['next_page']=1
                    return customers
                else:
                    es_query = {
                    "bool": {
                        "should": [

                            # Exact phrase match (highest priority)
                            {
                                "match_phrase": {
                                    "name": {
                                        "query": query,
                                        "boost": 5
                                    }
                                }
                            },

                            # Prefix search
                            {
                                "multi_match": {
                                    "query": query,
                                    "type": "phrase_prefix",
                                    "fields": ["name^3", "ui_id", "id"]
                                }
                            },

                            # Normal search
                            {
                                "multi_match": {
                                    "query": query,
                                    "fields": [
                                        "name^3",
                                        "ui_id",
                                        "id",
                                        "email",
                                        "mobile_number",
                                        "tenant_id",
                                        "secondary_domain",
                                        "sector",
                                        "industry"
                                    ],
                                    "fuzziness": "AUTO"
                                }
                            },

                            # Substring search
                            {
                                "wildcard": {
                                    "name": {
                                        "value": f"*{query}*",
                                        "case_insensitive": True
                                    }
                                }
                            }

                        ],
                        "minimum_should_match": 1
                    }
                }

                total_customers=await ES.count(
                    index=CUSTOMER_MODEL_NAME,
                    query=es_query
                )

                total = total_customers['count']
                total_pages = ceil(total / limit)
                if page>total_pages:
                    return "Page exists limit"
                next_page = page + 1 if page < total_pages else None

                res=await ES.search(
                    index=CUSTOMER_MODEL_NAME,
                    size=limit,
                    from_=(page-1)*limit,
                    _source=["id"],
                    query=es_query
                )

                ids = list(map(lambda x: x["_id"], res["hits"]["hits"]))
                
                customers=[]
                customers=await CustomersRepo(session=session,user_role=UserRoles.SUPER_ADMIN,cur_user_id="").get(limit=limit,in_search=ids,cursor=1)
                customers['next_page']=next_page
                customers['total_customers']=total
                return customers
            
        except (ConnectionTimeout,ConnectionError):
            return False
        
        except NotFoundError:
            ic("Not Found Fallback")
            customers=await CustomersRepo(session=session,user_role=UserRoles.SUPER_ADMIN,cur_user_id="").get(query=query,limit=limit,in_search=[],cursor=cursor)
            customers['next_page']=1
            return customers
