from . import HTTPException,BaseRepoModel
from ..models.distributor import DistributorsPayments
from ..models.product import Products
from ..models.order import Orders
from ..models.customer import Customers
from ..models.distributor import Distributors
from core.utils.uuid_generator import generate_uuid
from sqlalchemy import select,delete,update,or_,func,String,ARRAY,cast
from sqlalchemy.ext.asyncio import AsyncSession
from icecream import ic
from pydantic import EmailStr
from typing import Optional,List
from core.data_formats.enums.user_enums import UserRoles
from schemas.db_schemas.distributor_payment import AddDistributorPaymentDbSchema,UpdateDistributorPaymentDbSchema
from core.decorators.db_session_handler_dec import start_db_transaction
from math import ceil
from models.response_models.req_res_models import SuccessResponseTypDict,BaseResponseTypDict,ErrorResponseTypDict
from ..models.user import Users
from ..models.ui_id import TablesUiLId
from ..calculations import distri_additi_price,distri_disc_price,distributor_tot_price,distri_discount


class DistributorsPaymentsRepo(BaseRepoModel):
    def __init__(self,session:AsyncSession,user_role:UserRoles,cur_user_id:str):
        self.session=session
        self.user_role=user_role
        self.cur_user_id=cur_user_id
        self.distri_payment_info_cols=(
            DistributorsPayments.id,
            DistributorsPayments.sequence_id,
            DistributorsPayments.payment_infos,
            DistributorsPayments.distributor_id,
            DistributorsPayments.customer_id,
            DistributorsPayments.orders,
            DistributorsPayments.renewal_type,
            Customers.name.label("customer_name"),
            Distributors.name.label("distributor_name")

        )

        
    @start_db_transaction
    async def add(self,data:AddDistributorPaymentDbSchema):
        self.session.add(DistributorsPayments(**data.model_dump(mode='json')))
        return True
    
    # @start_db_transaction
    # async def add_bulk(self,datas:List[Distributors],lui_id:str):
    #     self.session.add_all(datas)
    #     await self.session.execute(update(TablesUiLId).where(TablesUiLId.id=="1").values(distri_luiid=lui_id))
    #     return True
        
    @start_db_transaction 
    async def update(self,data:UpdateDistributorPaymentDbSchema):
        data_toupdate=data.model_dump(mode='json',exclude=['id'],exclude_none=True,exclude_unset=True)

        if not data_toupdate or len(data_toupdate)<1:
            return ErrorResponseTypDict(status_code=400,success=False,msg="Error : Updating Distributor Payment",description="No valid fields to update provided")
        
        distributor_toupdate=update(DistributorsPayments).where(DistributorsPayments.id==data.id).values(
            **data_toupdate
        ).returning(DistributorsPayments.id)

        is_updated=(await self.session.execute(distributor_toupdate)).scalar_one_or_none()
        
        return is_updated if is_updated else ErrorResponseTypDict(status_code=400,success=False,msg="Error : Updating Distributor",description="Unable to update the distributor, may be invalid distributor id or no changes in data")
    

    @start_db_transaction
    async def delete(self,distri_payment_id:str,soft_delete:bool=True):
        ic(soft_delete)
        if soft_delete:
            distributor_todelete=update(DistributorsPayments).where(DistributorsPayments.id==distri_payment_id,DistributorsPayments.is_deleted==False).values(
                is_deleted=True,
                deleted_at=func.now(),
                deleted_by=self.cur_user_id
            ).returning(DistributorsPayments.id)
            is_deleted=(await self.session.execute(distributor_todelete)).scalar_one_or_none()

        else:
            if self.user_role if isinstance(self.user_role,UserRoles) else self.user_role!=UserRoles.SUPER_ADMIN.value:
                return ErrorResponseTypDict(status_code=403,success=False,msg="Error : Deleting Distributor Payment",description="Only super admin can perform hard delete operation")
            distributor_todelete=delete(DistributorsPayments).where(DistributorsPayments.id==distri_payment_id).returning(DistributorsPayments.id)
            is_deleted=(await self.session.execute(distributor_todelete)).scalar_one_or_none()
        return is_deleted if is_deleted else ErrorResponseTypDict(status_code=400,success=False,msg="Error : Deleting Distributor Payment",description="Unable to delete the distributor payment, may be invalid distributor payment id or distributor payment already deleted")
        
    @start_db_transaction
    async def recover(self,distri_payment_id:str):
        if self.user_role if isinstance(self.user_role,UserRoles) else self.user_role!=UserRoles.SUPER_ADMIN.value:
            return ErrorResponseTypDict(status_code=403,success=False,msg="Error : Recovering Distributor Payment",description="Only super admin can perform recover operation")
        
        distributor_torecover=update(DistributorsPayments).where(DistributorsPayments.id==distri_payment_id,DistributorsPayments.is_deleted==True).values(
            is_deleted=False
        ).returning(DistributorsPayments.id)
        is_recovered=(await self.session.execute(distributor_torecover)).scalar_one_or_none()
        return is_recovered if is_recovered else ErrorResponseTypDict(status_code=400,success=False,msg="Error : Recovering Distributor Payment",description="Unable to recover the distributor payment, may distributor payment is not deleted or already recovered")

    async def get(self,cursor:int=1,limit:int=10,query:str='',include_deleted:bool=False):
        search_term=f"%{query.lower()}%"
        date_expr=func.date(func.timezone("Asia/Kolkata",DistributorsPayments.created_at))
        deleted_at=func.date(func.timezone("Asia/Kolkata",DistributorsPayments.deleted_at))
        cursor=0 if cursor==1 else cursor
        cols=[*self.distri_payment_info_cols]
        if include_deleted:
            cols.extend([Users.name.label('deleted_by'),deleted_at.label('deleted_at')])

        orders_ids = (
            select(func.jsonb_array_elements_text(DistributorsPayments.orders))
            .correlate(DistributorsPayments)
        )
        orders_subquery = (
            select(
                func.json_agg(
                    func.json_build_object(
                        "id", Orders.id,
                        "order_ui_id", Orders.ui_id,
                        "product_name", Products.name,
                        "product_price", Products.price,
                        "product_id", Orders.product_id,
                        "quantity", Orders.quantity,
                        "distri_discount_price", distri_disc_price,
                        "distri_additi_price", distri_additi_price,
                        "distributor_total_price", distributor_tot_price,
                    )
                )
            )
            .select_from(Orders)
            .join(Products, Products.id == Orders.product_id)   # ✅ MUST
            .where(
                Orders.id.in_(orders_ids)
                
            )
            .correlate(DistributorsPayments)
            .scalar_subquery()
        )
        queried_distri = (await self.session.execute(
            select(
                *cols,
                date_expr.label("created_at"),
                orders_subquery.label("selected_products")
            )
            .select_from(DistributorsPayments)  # ✅ FIXED
            .join(Customers, DistributorsPayments.customer_id == Customers.id, isouter=True)
            .join(Distributors, DistributorsPayments.distributor_id == Distributors.id, isouter=True)
            .where(
                or_(
                    func.cast(DistributorsPayments.id, String).ilike(search_term),
                    func.cast(DistributorsPayments.created_at, String).ilike(search_term),
                ),
                DistributorsPayments.sequence_id > cursor,
                DistributorsPayments.is_deleted == include_deleted
            )
            .order_by(
                DistributorsPayments.id,
                DistributorsPayments.sequence_id.asc()
            )
        )).mappings().all()

        ic(queried_distri)

        total_distributors:int=0
        if cursor==0:
            total_distributors=(await self.session.execute(
                select(func.count(DistributorsPayments.id)).where(DistributorsPayments.is_deleted==False)
            )).scalar_one_or_none()

        return {
            'distributors_payments':queried_distri,
            'total_distributors_payments':total_distributors,
            'total_pages':ceil(total_distributors/limit),
            'next_cursor':queried_distri[-1]['sequence_id'] if len(queried_distri)>1 else None
        }
        
    
    async def search(self,query:str):
        search_term=f"%{query.lower()}%"
        queried_distributors=(await self.session.execute(
            select(
                *self.distri_payment_info_cols
            ).where(
                or_(
                    func.cast(DistributorsPayments.id,String).ilike(search_term),
                    func.cast(DistributorsPayments.created_at,String).ilike(search_term),
                ),
                DistributorsPayments.is_deleted==False
            )
            .limit(5)
        )).mappings().all()

        return {'distributors_payments':queried_distributors}

       
    async def get_by_id(self,distributor_payment_id:str):
        date_expr=func.date(func.timezone("Asia/Kolkata",DistributorsPayments.created_at))
        orders_ids = (
            select(func.jsonb_array_elements_text(DistributorsPayments.orders))
            .correlate(DistributorsPayments)
        )
        orders_subquery = (
            select(
                func.json_agg(
                    func.json_build_object(
                        "id", Orders.id,
                        "order_ui_id", Orders.ui_id,
                        "product_name", Products.name,
                        "product_price", Products.price,
                        "product_id", Orders.product_id,
                        "quantity", Orders.quantity,
                        "distri_discount_price", distri_disc_price,
                        "distri_additi_price", distri_additi_price,
                        "distributor_total_price", distributor_tot_price,
                    )
                )
            )
            .select_from(Orders)
            .join(Products, Products.id == Orders.product_id)   # ✅ MUST
            .where(
                Orders.id.in_(orders_ids),
            )
            .correlate(DistributorsPayments)
            .scalar_subquery()
        )
        queried_distri = (await self.session.execute(
            select(
                *self.distri_payment_info_cols,
                date_expr.label("created_at"),
                orders_subquery.label("selected_products")
            )
            .select_from(DistributorsPayments)  # ✅ FIXED
            .join(Customers, DistributorsPayments.customer_id == Customers.id, isouter=True)
            .join(Distributors, DistributorsPayments.distributor_id == Distributors.id, isouter=True)
            .where(
                DistributorsPayments.id==distributor_payment_id,
                DistributorsPayments.is_deleted == False
            )
            .order_by(
                DistributorsPayments.id,
                DistributorsPayments.sequence_id.asc()
            )
        )).mappings().one_or_none()
        
        return {'distributors_payments':queried_distri}


