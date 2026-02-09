from . import HTTPException,BaseRepoModel
from ..models.distributor import Distributors
from ..models.product import Products,ProductTypes
from core.utils.uuid_generator import generate_uuid
from sqlalchemy import select,delete,update,or_,func,String
from sqlalchemy.ext.asyncio import AsyncSession
from icecream import ic
from pydantic import EmailStr
from typing import Optional,List
from core.data_formats.enums.common_enums import UserRoles
from schemas.db_schemas.distributor import CreateDistriDbSchema,UpdateDistriDbSchema
from core.decorators.db_session_handler_dec import start_db_transaction
from math import ceil
from models.response_models.req_res_models import SuccessResponseTypDict,BaseResponseTypDict,ErrorResponseTypDict
from ..models.user import Users
from ..models.ui_id import TablesUiLId


class DistributorsRepo(BaseRepoModel):
    def __init__(self,session:AsyncSession,user_role:UserRoles,cur_user_id:str):
        self.session=session
        self.user_role=user_role
        self.cur_user_id=cur_user_id
        self.distri_cols=(
            Distributors.sequence_id,
            Distributors.id,
            Distributors.ui_id,
            Distributors.name,
            Distributors.discount
        )

        
    @start_db_transaction
    async def add(self,data:CreateDistriDbSchema):
        self.session.add(Distributors(**data.model_dump(mode='json',exclude=['lui_id'])))
        await self.session.execute(update(TablesUiLId).where(TablesUiLId.id=="1").values(distri_luiid=data.ui_id))
        return True
    
    @start_db_transaction
    async def add_bulk(self,datas:List[Distributors],lui_id:str):
        self.session.add_all(datas)
        await self.session.execute(update(TablesUiLId).where(TablesUiLId.id=="1").values(distri_luiid=lui_id))
        return True
        
    @start_db_transaction  
    async def update(self,data:UpdateDistriDbSchema):
        data_toupdate=data.model_dump(mode='json',exclude=['id'],exclude_none=True,exclude_unset=True)

        if not data_toupdate or len(data_toupdate)<1:
            return ErrorResponseTypDict(status_code=400,success=False,msg="Error : Updating Distributor",description="No valid fields to update provided")
        
        distributor_toupdate=update(Distributors).where(Distributors.id==data.id).values(
            **data_toupdate
        ).returning(Distributors.id)

        is_updated=(await self.session.execute(distributor_toupdate)).scalar_one_or_none()
        
        return is_updated if is_updated else ErrorResponseTypDict(status_code=400,success=False,msg="Error : Updating Distributor",description="Unable to update the distributor, may be invalid distributor id or no changes in data")
    

    @start_db_transaction
    async def delete(self,distri_id:str,soft_delete:bool=True):
        ic(soft_delete)
        if soft_delete:
            distributor_todelete=update(Distributors).where(Distributors.id==distri_id,Distributors.is_deleted==False).values(
                is_deleted=True,
                deleted_at=func.now(),
                deleted_by=self.cur_user_id
            ).returning(Distributors.id)
            is_deleted=(await self.session.execute(distributor_todelete)).scalar_one_or_none()

        else:
            if self.user_role if isinstance(self.user_role,UserRoles) else self.user_role!=UserRoles.SUPER_ADMIN.value:
                return ErrorResponseTypDict(status_code=403,success=False,msg="Error : Deleting Distributor",description="Only super admin can perform hard delete operation")
            distributor_todelete=delete(Distributors).where(Distributors.id==distri_id).returning(Distributors.id)
            is_deleted=(await self.session.execute(distributor_todelete)).scalar_one_or_none()
        return is_deleted if is_deleted else ErrorResponseTypDict(status_code=400,success=False,msg="Error : Deleting Distributor",description="Unable to delete the distributor, may be invalid distributor id or distributor already deleted")
        
    @start_db_transaction
    async def recover(self,distri_id:str):
        if self.user_role if isinstance(self.user_role,UserRoles) else self.user_role!=UserRoles.SUPER_ADMIN.value:
            return ErrorResponseTypDict(status_code=403,success=False,msg="Error : Recovering Distributor",description="Only super admin can perform recover operation")
        
        distributor_torecover=update(Distributors).where(Distributors.id==distri_id,Distributors.is_deleted==True).values(
            is_deleted=False
        ).returning(Distributors.id)
        is_recovered=(await self.session.execute(distributor_torecover)).scalar_one_or_none()
        return is_recovered if is_recovered else ErrorResponseTypDict(status_code=400,success=False,msg="Error : Recovering Distributor",description="Unable to recover the distributor, may distributor is not deleted or already recovered")

    async def get(self,cursor:int=1,limit:int=10,query:str='',include_deleted:bool=False):
        search_term=f"%{query.lower()}%"
        date_expr=func.date(func.timezone("Asia/Kolkata",Distributors.created_at))
        deleted_at=func.date(func.timezone("Asia/Kolkata",Distributors.deleted_at))
        cols=[*self.distri_cols]
        if include_deleted:
            cols.extend([Users.name.label('deleted_by'),deleted_at.label('deleted_at')])

        queried_distri=(await self.session.execute(
            select(
                *cols,
                date_expr.label("created_at")
            ).limit(limit)
            .join(Users,Users.id==Distributors.deleted_by,isouter=True)
            .where(
                or_(
                    Distributors.id.ilike(search_term),
                    Distributors.name.ilike(search_term),
                    func.cast(Distributors.created_at,String).ilike(search_term),

                ),
                Distributors.sequence_id>cursor,
                Distributors.is_deleted==include_deleted
            ).order_by(Distributors.sequence_id.asc())
        )).mappings().all()

        total_distributors:int=0
        if cursor==1:
            total_distributors=(await self.session.execute(
                select(func.count(Distributors.id)).where(Distributors.is_deleted==False)
            )).scalar_one_or_none()

        return {
            'distributors':queried_distri,
            'total_distributors':total_distributors,
            'total_pages':ceil(total_distributors/limit),
            'next_cursor':queried_distri[-1]['sequence_id'] if len(queried_distri)>1 else None
        }
        
    
    async def search(self,query:str):
        search_term=f"%{query.lower()}%"
        queried_distributors=(await self.session.execute(
            select(
                Distributors.id,
                Distributors.name,
                Distributors.discount
            ).where(
                or_(
                    Distributors.id.ilike(search_term),
                    Distributors.name.ilike(search_term),
                    func.cast(Distributors.created_at,String).ilike(search_term)
                ),
                Distributors.is_deleted==False
            )
            .limit(5)
        )).mappings().all()

        return {'distributors':queried_distributors}

       
    async def get_by_id(self,distributor_id:str):
        date_expr=func.date(func.timezone("Asia/Kolkata",Distributors.created_at))
        queried_distributors=(await self.session.execute(
            select(
                *self.distri_cols,
                date_expr.label("created_at")
            )
            .where(Distributors.id==distributor_id,Distributors.is_deleted==False)
        )).mappings().one_or_none()
        
        return {'distributors':queried_distributors}



