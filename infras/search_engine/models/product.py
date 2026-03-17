from ..main import ES
from icecream import ic
from typing import List
from elasticsearch.helpers import async_bulk,BulkIndexError
from ...primary_db.repos.product_repo import ProductsRepo,UserRoles
from elasticsearch import NotFoundError,ConnectionError,ConnectionTimeout
from ...primary_db.main import AsyncLocalSession
from math import ceil

PRODUCT_MODEL_NAME="products"


class ProductSearch:
    async def create_index(self):
        exists=await ES.indices.exists(index=PRODUCT_MODEL_NAME)
        if not exists:
            res=await ES.indices.create(index=PRODUCT_MODEL_NAME,ignore=400)
            ic(res)
        return True

    async def create_document(self,data:dict):
        try:
            res=await ES.index(
                index=PRODUCT_MODEL_NAME,
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
                    '_index':PRODUCT_MODEL_NAME,
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
                index=PRODUCT_MODEL_NAME,
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
                    '_index':PRODUCT_MODEL_NAME,
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
                index=PRODUCT_MODEL_NAME,
                id=id
            )

            ic(res)

            return res
        except (ConnectionTimeout,ConnectionError):
            return False
    

    async def delete_bulk_doc(self,ids:List[dict]):
        def generate_actions():
            for id in ids:
                yield {
                    'op_type':'delete',
                    '_id':id,
                    '_index':PRODUCT_MODEL_NAME,
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
                    products=await ProductsRepo(session=session,user_role=UserRoles.SUPER_ADMIN,cur_user_id="").get(limit=limit,in_search=[],cursor=cursor)
                    products['next_page']=1
                    return products
                else:
                    es_query={
                        "bool": {
                            "should": [
                                {
                                    "multi_match": {
                                        "query": query,
                                        "fields": ["ui_id"],
                                    }
                                },
                                {
                                    "multi_match": {
                                        "query": query,
                                        "fields": ["id","name","description","part_number","product_type"],
                                        "fuzziness": "AUTO"
                                    }
                                },
                                {
                                    "multi_match": {
                                        "query": query,
                                        "type": "phrase_prefix",
                                        "fields": ["ui_id","name","description","id","part_number","product_type"]
                                    }
                                }
                            ]
                        }
                    }
                
                total_products=await ES.count(
                    index=PRODUCT_MODEL_NAME,
                    query=es_query
                )

                total = total_products['count']
                total_pages = ceil(total / limit)

                if page>total_pages:
                    return "Page exists limit"

                next_page = page + 1 if page < total_pages else None
                res=await ES.search(
                    index=PRODUCT_MODEL_NAME,
                    size=limit,
                    from_=(page-1)*limit,
                    _source=["id"],
                    query=es_query
                )

                ic(res)
                ids = list(map(lambda x: x["_id"], res["hits"]["hits"]))
                
                
                products=await ProductsRepo(session=session,user_role=UserRoles.SUPER_ADMIN,cur_user_id="").get(limit=limit,in_search=ids,cursor=1)
                products['total_products']=total
                products['next_page']=next_page
                return products
        except (ConnectionTimeout,ConnectionError):
            return False   
        except NotFoundError:
            ic("Not Found Fallback")
            products=await ProductsRepo(session=session,user_role=UserRoles.SUPER_ADMIN,cur_user_id="").get(query=query,limit=limit,in_search=[],cursor=cursor)
            products['next_page']=1
            return products