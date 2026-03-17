from ..main import ES
from icecream import ic
from typing import List
from elasticsearch.helpers import async_bulk,BulkIndexError
from ...primary_db.repos.order_repo import OrdersRepo,UserRoles
from ...primary_db.main import AsyncLocalSession
from schemas.request_schemas.order import OrderFilterSchema
from elasticsearch import NotFoundError,ConnectionError,ConnectionTimeout
from math import ceil
ORDER_MODEL_NAME="orders"


class OrderSearch:
    async def create_index(self):
        exists=await ES.indices.exists(index=ORDER_MODEL_NAME)
        if not exists:
            res=await ES.indices.create(index=ORDER_MODEL_NAME,ignore=400)
            ic(res)
        return True

    async def create_document(self,data:dict):
        try:
            res=await ES.index(
                index=ORDER_MODEL_NAME,
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
                    '_index':ORDER_MODEL_NAME,
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
                index=ORDER_MODEL_NAME,
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
                    '_index':ORDER_MODEL_NAME,
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
                index=ORDER_MODEL_NAME,
                id=id
            )

            ic(res)

            return res
        except (ConnectionTimeout,ConnectionError):
            return False
    

    async def delete_bulk_doc(self,ids:List[str]):
        def generate_actions():
            for id in ids:
                yield {
                    'op_type':'delete',
                    '_id':id,
                    '_index':ORDER_MODEL_NAME,
                }
        try:
            res=await async_bulk(ES,generate_actions(),chunk_size=1000)
            ic(res)

            return res
        except (ConnectionTimeout,ConnectionError):
            return False
    
    async def search_document(self,query:str,limit:int,page:int,cursor:int,filter:OrderFilterSchema):
        try:
            async with AsyncLocalSession() as session:
                if not query or not query.strip():
                    ic("inside match all")
                    orders=await OrdersRepo(session=session,user_role=UserRoles.SUPER_ADMIN,cur_user_id="").get(limit=limit,in_search=[],cursor=cursor,filter=filter)
                    orders['next_page']=1
                    return orders
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
                                        "fields": ["id","name","email","mobile_number","tenant_id","secondary_domain","sector","industry"],
                                        "fuzziness": "AUTO"
                                    }
                                },
                                {
                                    "multi_match": {
                                        "query": query,
                                        "type": "phrase_prefix",
                                        "fields": ["ui_id","id","name","email","mobile_number","tenant_id","secondary_domain","sector","industry"]
                                    }
                                }
                            ]
                        }
                    }

                total_orders=await ES.count(
                    index=ORDER_MODEL_NAME,
                    query=es_query
                )

                total = total_orders['count']
                total_pages = ceil(total / limit)

                if page>total_pages:
                    return "Page exists limit"

                next_page = page + 1 if page < total_pages else None

                res=await ES.search(
                    index=ORDER_MODEL_NAME,
                    size=limit,
                    from_=(page-1)*limit,
                    _source=["id"],
                    query=es_query
                )

                ic(res)
                ids = list(map(lambda x: x["_id"], res["hits"]["hits"]))
                ic(ids)
                
                orders=await OrdersRepo(session=session,user_role=UserRoles.SUPER_ADMIN,cur_user_id="").get(limit=limit,in_search=ids,cursor=cursor,filter=filter)
                orders['next_page']=next_page
                orders['total_orders']=total
                return orders
        except (ConnectionTimeout,ConnectionError):
            return False
        except NotFoundError:
            ic("Not Found Fallback")
            orders=await OrdersRepo(session=session,user_role=UserRoles.SUPER_ADMIN,cur_user_id="").get(query=query,limit=limit,in_search=[],cursor=cursor,filter=filter)
            orders['next_page']=1
            return orders
