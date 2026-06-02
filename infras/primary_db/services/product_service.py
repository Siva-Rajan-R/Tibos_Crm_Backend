from . import BaseServiceModel
from ..models.product import Products
from ..models.order import Orders
from core.utils.uuid_generator import generate_uuid
from .activity_log_service import ActivityLogService
from sqlalchemy import select,delete,update,or_,cast,String,func,Float
from sqlalchemy.ext.asyncio import AsyncSession
from icecream import ic
from core.data_formats.enums.user_enums import UserRoles
from core.decorators.error_handler_dec import catch_errors
from ..repos.product_repo import ProductsRepo
from schemas.db_schemas.product import AddProductDbSchema,UpdateProductDbSchema
from schemas.request_schemas.product import AddProductSchema,UpdateProductSchema,AddSearchFields,UpdateSearchFields
from math import ceil
from typing import Optional,List
from models.response_models.req_res_models import SuccessResponseTypDict,BaseResponseTypDict,ErrorResponseTypDict
from ..models.ui_id import TablesUiLId
from core.utils.ui_id_generator import generate_ui_id
from core.constants import UI_ID_STARTING_DIGIT,LUI_ID_PRODUCT_PREFIX
from ...search_engine.models.product import ProductSearch


class ProductsService(BaseServiceModel):
    def __init__(self,session:AsyncSession,user_role:UserRoles,cur_user_id:str):
        self.session=session
        self.user_role=user_role
        self.cur_user_id=cur_user_id
        
    @catch_errors
    async def add(self,data:AddProductSchema):
        # if (await ProductsRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).get_by_part_number(part_number=data.part_number)):
        #     return ErrorResponseTypDict(status_code=400,success=False,msg="Error : Adding Product",description="Product with the given part number already exists")
        prod_id:str=generate_uuid()
        lui_id:str=(await self.session.execute(select(TablesUiLId.product_luiid))).scalar_one_or_none()
        cur_uiid=generate_ui_id(prefix=LUI_ID_PRODUCT_PREFIX,last_id=lui_id)

        search_fields=AddSearchFields(
            ui_id=cur_uiid,
            id=prod_id,
            name=data.name,
            description=data.description,
            part_number=data.part_number,
            product_type=data.product_type
        ).model_dump(mode="json")

        # await ProductSearch().create_document(data=search_fields)

        result = await ProductsRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).add(data=AddProductDbSchema(**data.model_dump(mode='json'),id=prod_id,ui_id=cur_uiid))
        if result and not isinstance(result, dict) or (isinstance(result, dict) and result.get("success") is not False):
            await ActivityLogService(self.session, self.user_role, self.cur_user_id).log_action(
                action="CREATE_MANUAL",
                entity_type="PRODUCT",
                entity_id=prod_id,
                details={"name": data.name, "part_number": data.part_number}
            )
        return result

    @catch_errors
    async def add_bulk(self,datas:List[dict]):
        datas_toadd=[]
        skipped_items=[]
        searchable_datas=[]

        lui_id:str=(await self.session.execute(select(TablesUiLId.product_luiid))).scalar_one_or_none()
        for data in datas:
            ic(data)
            # if (await ProductsRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).get_by_part_number(part_number=data.get('part_number'))):
            #     skipped_items.append(data)
            #     continue

            prod_id:str=generate_uuid()
            cur_uiid=generate_ui_id(prefix=LUI_ID_PRODUCT_PREFIX,last_id=lui_id)
            ic("Before increment : ",lui_id)
            lui_id=cur_uiid
            ic("After increment : ",lui_id)
            search_fields=AddSearchFields(
                ui_id=cur_uiid,
                id=prod_id,
                name=data['name'],
                description=data['description'],
                part_number=data['part_number'],
                product_type=data['product_type']
            ).model_dump(mode="json")

            searchable_datas.append(search_fields)
            datas_toadd.append(Products(**data,id=prod_id,ui_id=cur_uiid))
            
        ic(datas_toadd,skipped_items)
        # await ProductSearch().create_bulk_doc(datas=searchable_datas)
        result = await ProductsRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).add_bulk(datas=datas_toadd,lui_id=lui_id)
        if result and not isinstance(result, dict) or (isinstance(result, dict) and result.get("success") is not False):
            added_ids = [d.id for d in datas_toadd]
            if added_ids:
                await ActivityLogService(self.session, self.user_role, self.cur_user_id).log_bulk_actions(
                    action="CREATE_EXCEL",
                    entity_type="PRODUCT",
                    entity_ids=added_ids
                )
        return result

    @catch_errors   
    async def update(self,data:UpdateProductDbSchema):
        data_toupdate=data.model_dump(mode='json',exclude_none=True,exclude_unset=True)
        if not data_toupdate or len(data_toupdate)<1:
            return ErrorResponseTypDict(status_code=400,success=False,msg="Error : Updating Product",description="No valid fields to update provided")
        
        search_fields=UpdateSearchFields(
            name=data.name,
            description=data.description,
            part_number=data.part_number,
            product_type=data.product_type
        ).model_dump(mode="json")

        # await ProductSearch().update_document(data=search_fields,id=data.product_id)
        from sqlalchemy import select
        from ..models.product import Products
        from fastapi.encoders import jsonable_encoder
        old_record = (await self.session.execute(select(Products).where(Products.id == data.product_id))).scalar_one_or_none()
        old_values = {}
        new_values = {}
        if old_record:
            for key, new_val in data_toupdate.items():
                if not hasattr(old_record, key):
                    continue
                old_val_raw = getattr(old_record, key)
                old_val = jsonable_encoder(old_val_raw)
                if old_val != new_val:
                    old_values[key] = old_val if old_val is not None else None
                    new_values[key] = new_val if new_val is not None else None

        result = await ProductsRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).update(data=UpdateProductDbSchema(**data_toupdate))
        if result and not isinstance(result, dict) or (isinstance(result, dict) and result.get("success") is not False):
            details = {"updated_fields": list(data_toupdate.keys())}
            if old_values or new_values:
                details["old_values"] = old_values
                details["new_values"] = new_values

            await ActivityLogService(self.session, self.user_role, self.cur_user_id).log_action(
                action="UPDATE",
                entity_type="PRODUCT",
                entity_id=data.product_id,
                details=details
            )
        return result

    @catch_errors
    async def recover(self,product_torecover:str):
        product=await self.get_by_id(product_id=product_torecover,include_delete=True)
        product_info=product['product']
        search_fields=AddSearchFields(
            ui_id=product_info['ui_id'],
            id=product_info['id'],
            name=product_info['name'],
            description=product_info['description'],
            part_number=product_info['part_number'],
            product_type=product_info['product_type']
        ).model_dump(mode="json")

        # await ProductSearch().create_document(data=search_fields)

        result = await ProductsRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).recover(product_torecover=product_torecover)
        if result and not isinstance(result, dict) or (isinstance(result, dict) and result.get("success") is not False):
            await ActivityLogService(self.session, self.user_role, self.cur_user_id).log_action(
                action="RECOVER",
                entity_type="PRODUCT",
                entity_id=product_torecover
            )
        return result

    @catch_errors
    async def delete(self,product_id:str,soft_delete:bool=True):
        # await ProductSearch().delete_document(id=product_id)
        result = await ProductsRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).delete(product_id=product_id,soft_delete=soft_delete)
        if result and not isinstance(result, dict) or (isinstance(result, dict) and result.get("success") is not False):
            await ActivityLogService(self.session, self.user_role, self.cur_user_id).log_action(
                action="DELETE",
                entity_type="PRODUCT",
                entity_id=product_id,
                details={"soft_delete": soft_delete}
            )
        return result

    @catch_errors   
    async def get(self,cursor:int=1,limit:int=10,query:str='',include_deleted:Optional[bool]=False):
        return await ProductsRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).get(cursor=cursor,limit=limit,query=query,include_deleted=include_deleted)
    
    @catch_errors
    async def search(self, query: str):
        return await ProductsRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).search(query=query)
    
    @catch_errors
    async def get_by_id(self,product_id:str,include_delete:bool=False):
        return await ProductsRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).get_by_id(product_id=product_id,include_delete=include_delete)



