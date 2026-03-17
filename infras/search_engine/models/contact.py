from ..main import ES
from icecream import ic
from typing import List
from elasticsearch.helpers import async_bulk,BulkIndexError
from ...primary_db.repos.contact_repo import ContactsRepo,UserRoles
from ...primary_db.main import AsyncLocalSession
from elasticsearch import NotFoundError
from math import ceil
from elasticsearch import NotFoundError,ConnectionTimeout,ConnectionError

CONTACT_MODEL_NAME="contacts"


class ContactSearch:
    async def create_index(self):
        exists=await ES.indices.exists(index=CONTACT_MODEL_NAME)
        if not exists:
            res=await ES.indices.create(index=CONTACT_MODEL_NAME,ignore=400)
            ic(res)
        return True

    async def create_document(self,data:dict):
        try:
            res=await ES.index(
                index=CONTACT_MODEL_NAME,
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
                    '_index':CONTACT_MODEL_NAME,
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
                index=CONTACT_MODEL_NAME,
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
                    '_index':CONTACT_MODEL_NAME,
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
                index=CONTACT_MODEL_NAME,
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
                    '_index':CONTACT_MODEL_NAME,
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
                    contacts=await ContactsRepo(session=session,user_role=UserRoles.SUPER_ADMIN,cur_user_id="").get(cursor=cursor,limit=limit,in_search=[])
                    contacts['next_page']=1
                    return contacts
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
                                        "fields": ["id","name","email","mobile_number","customer_email","customer_name","customer_id"],
                                        "fuzziness": "AUTO"
                                    }
                                },
                                {
                                    "multi_match": {
                                        "query": query,
                                        "type": "phrase_prefix",
                                        "fields": ["ui_id","id","name","email","mobile_number","customer_email","customer_name","customer_id"]
                                    }
                                }
                            ]
                        }
                    }


                total_contacts=await ES.count(
                    index=CONTACT_MODEL_NAME,
                    query=es_query
                )

                total = total_contacts['count']
                total_pages = ceil(total / limit)

                if page>total_pages:
                    return "Page exists limit"

                next_page = page + 1 if page < total_pages else None
                res=await ES.search(
                    index=CONTACT_MODEL_NAME,
                    size=limit,
                    from_=(page-1)*limit,
                    _source=["id"],
                    query=es_query
                )

                ids = list(map(lambda x: x["_id"], res["hits"]["hits"]))
                ic(ids)
                
                contacts=await ContactsRepo(session=session,user_role=UserRoles.SUPER_ADMIN,cur_user_id="").get(cursor=cursor,limit=limit,in_search=ids)
                ic(contacts)
                ic(total_contacts)
                
                contacts['next_page']=next_page
                contacts['total_contacts']=total_contacts['count']
                return contacts
        
        except (ConnectionTimeout,ConnectionError):
            return False
        
        except NotFoundError:
            ic("Not Found Fallback")
            contacts=await ContactsRepo(session=session,user_role=UserRoles.SUPER_ADMIN,cur_user_id="").get(query=query,cursor=cursor,limit=limit,in_search=[])
            contacts['next_page']=1
            return contacts
