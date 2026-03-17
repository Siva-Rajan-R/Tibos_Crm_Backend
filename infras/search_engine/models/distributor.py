from ..main import ES
from icecream import ic
from typing import List
from elasticsearch.helpers import async_bulk,BulkIndexError
from elasticsearch import NotFoundError,ConnectionError,ConnectionTimeout
from ...primary_db.repos.distri_repo import DistributorsRepo,UserRoles
from ...primary_db.main import AsyncLocalSession
from math import ceil
DISTRIBUTOR_MODEL_NAME="distributors"


class DistributorSearch:
    async def create_index(self):
        exists=await ES.indices.exists(index=DISTRIBUTOR_MODEL_NAME)
        if not exists:
            res=await ES.indices.create(index=DISTRIBUTOR_MODEL_NAME,ignore=400)
            ic(res)
        return True

    async def create_document(self,data:dict):
        try:
            res=await ES.index(
                index=DISTRIBUTOR_MODEL_NAME,
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
                    '_index':DISTRIBUTOR_MODEL_NAME,
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
                index=DISTRIBUTOR_MODEL_NAME,
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
                    '_index':DISTRIBUTOR_MODEL_NAME,
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
                index=DISTRIBUTOR_MODEL_NAME,
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
                    '_index':DISTRIBUTOR_MODEL_NAME,
                }
        try:
            res=await async_bulk(ES,generate_actions(),chunk_size=1000)
            ic(res)

            return res
        
        except (ConnectionTimeout,ConnectionError):
            return False
        
    async def search_document(self,query:str,limit:int,page:int,cursor:int):
        async with AsyncLocalSession() as session:
            try:
                if not query or not query.strip():
                    distributors=await DistributorsRepo(session=session,user_role=UserRoles.SUPER_ADMIN,cur_user_id="").get(cursor=cursor,limit=limit,in_search=[])
                    distributors['next_page']=1
                    return distributors
                else:
                    es_query={
                        "bool": {
                            "should": [
                                {
                                    "wildcard": {
                                        "name": {
                                        "value": f"*{query.lower()}*",
                                        "case_insensitive": True
                                        }
                                    }
                                },
                                {
                                    "multi_match": {
                                        "query": query,
                                        "fields": ["ui_id"],
                                    }
                                },
                                {
                                    "multi_match": {
                                        "query": query,
                                        "fields": ["id","name"],
                                        
                                    }
                                },
                                {
                                    "multi_match": {
                                        "query": query,
                                        "type": "phrase_prefix",
                                        "fields": ["name","ui_id",'id']
                                    }
                                }
                            ]
                        }
                    }

                total_distributors =await ES.count(
                    index=DISTRIBUTOR_MODEL_NAME,
                    query=es_query
                )

                total = total_distributors['count']
                total_pages = ceil(total / limit)

                if page>total_pages:
                    return "Page exists limit"

                next_page = page + 1 if page < total_pages else None

                res=await ES.search(
                    index=DISTRIBUTOR_MODEL_NAME,
                    size=limit,
                    from_=(page-1)*limit,
                    _source=["id"],
                    query=es_query
                )
                ids = list(map(lambda x: x["_id"], res["hits"]["hits"]))
                
                distributors=await DistributorsRepo(session=session,user_role=UserRoles.SUPER_ADMIN,cur_user_id="").get(cursor=cursor,limit=limit,in_search=ids)
                distributors['next_page']=next_page
                distributors['total_distributors']=total
                return distributors
            except (ConnectionTimeout,ConnectionError):
                return False
            except NotFoundError:
                ic("Not Found Fallback")
                distributors=await DistributorsRepo(session=session,user_role=UserRoles.SUPER_ADMIN,cur_user_id="").get(query=query,cursor=cursor,limit=limit,in_search=[])
                distributors['next_page']=1
                return distributors

