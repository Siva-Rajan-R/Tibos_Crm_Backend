from . import HTTPException,BaseRepoModel
from ..models.customer import Customers,CustomerIndustries,CustomerSectors
from core.utils.uuid_generator import generate_uuid
from ..models.order import Orders
from sqlalchemy import select,delete,update,or_,func,String
from sqlalchemy.ext.asyncio import AsyncSession
from icecream import ic
from core.data_formats.enums.common_enums import UserRoles
from pydantic import EmailStr
from typing import Optional,List
from schemas.db_schemas.customer import AddCustomerDbSchema,UpdateCustomerDbSchema
from core.decorators.db_session_handler_dec import start_db_transaction
from math import ceil
from ..models.user import Users
from models.response_models.req_res_models import SuccessResponseTypDict,BaseResponseTypDict,ErrorResponseTypDict
from ..models.ui_id import TablesUiLId



class CustomersRepo(BaseRepoModel):
    def __init__(self,session:AsyncSession,user_role:UserRoles,cur_user_id:str):
        self.session=session
        self.user_role=user_role
        self.cur_user_id=cur_user_id
        self.customer_cols=(
            Customers.sequence_id,
            Customers.id,
            Customers.ui_id,
            Customers.name,
            Customers.mobile_number,
            Customers.email,
            Customers.gst_number,
            Customers.no_of_employee,
            Customers.website_url,
            Customers.industry,
            Customers.sector,
            Customers.address,
            Customers.owner,
            Customers.tenant_id
        )

    async def is_customer_exists(self,email:EmailStr,mobile_number:str):
        is_exists=(await self.session.execute(
            select(Customers.id)
            .where(
                or_(
                    Customers.email==email,
                    Customers.mobile_number==mobile_number
                ),
                Customers.is_deleted==False
            )
        )).scalar_one_or_none()

        return is_exists

        
    @start_db_transaction
    async def add(self,data:AddCustomerDbSchema):

        self.session.add(Customers(**data.model_dump(mode='json',exclude=['lui_id'])))
    
        await self.session.execute(update(TablesUiLId).where(TablesUiLId.id=="1").values(customer_luiid=data.ui_id))

        return True
    
    @start_db_transaction
    async def add_bulk(self,datas:List[Customers]):
        self.session.add_all(datas)
        return True
        
    @start_db_transaction  
    async def update(self,data:UpdateCustomerDbSchema):
        data_toupdate=data.model_dump(mode='json',exclude=['customer_id'],exclude_none=True,exclude_unset=True)

        if not data_toupdate or len(data_toupdate)<1:
            return ErrorResponseTypDict(status_code=400,success=False,msg="Error : Updating Customer",description="No data provided for update")
        
        customer_toupdate=update(Customers).where(Customers.id==data.customer_id).values(
            **data_toupdate
        ).returning(Customers.id)

        is_updated=(await self.session.execute(customer_toupdate)).scalar_one_or_none()
        
        return is_updated if is_updated else ErrorResponseTypDict(status_code=400,success=False,msg="Error : Updating Customer",description="Unable to update the customer, may be invalid customer or customer may not exist")
        
    @start_db_transaction
    async def delete(self,customer_id:str,soft_delete:bool=True):
        have_order=(await self.session.execute(select(Orders.id).where(Orders.customer_id==customer_id).limit(1))).scalar_one_or_none()
        if have_order:
            return ErrorResponseTypDict(status_code=400,success=False,msg="Error : Deleting Customer",description="Cannot delete customer with existing orders. Please delete associated orders first.")

        if soft_delete:
            customer_todelete=update(Customers).where(Customers.id==customer_id,Customers.is_deleted==False).values(
                is_deleted=True,
                deleted_at=func.now(),
                deleted_by=self.cur_user_id
            ).returning(Customers.id)
            is_deleted=(await self.session.execute(customer_todelete)).scalar_one_or_none()

        else:
            if self.user_role if isinstance(self.user_role,UserRoles) else self.user_role!=UserRoles.SUPER_ADMIN.value:
                return ErrorResponseTypDict(status_code=403,success=False,msg="Error : Deleting Customer",description="Only super admin can perform hard delete operation")
            customer_todelete=delete(Customers).where(Customers.id==customer_id).returning(Customers.id)
            is_deleted=(await self.session.execute(customer_todelete)).scalar_one_or_none()
            
        return is_deleted if is_deleted else ErrorResponseTypDict(status_code=400,success=False,msg="Error : Deleting Customer",description="Unable to delete the customer, may be invalid customer id or customer already deleted")
        
    @start_db_transaction
    async def recover(self,customer_id:str):
        if self.user_role if isinstance(self.user_role,UserRoles) else self.user_role!=UserRoles.SUPER_ADMIN.value:
            return ErrorResponseTypDict(status_code=403,success=False,msg="Error : Recovering Customer",description="Only super admin can perform recover operation")
        
        customer_torecover=update(Customers).where(Customers.id==customer_id,Customers.is_deleted==True).values(
            is_deleted=False
        ).returning(Customers.id)
        is_recovered=(await self.session.execute(customer_torecover)).scalar_one_or_none()
        return is_recovered if is_recovered else ErrorResponseTypDict(status_code=400,success=False,msg="Error : Recovering Customer",description="Unable to recover the customer, may customer is not deleted or already recovered")
        

    async def get(self,cursor:int=1,limit:int=10,query:str='',include_deleted:bool=False):
        search_term=f"%{query.lower()}%"
        date_expr=func.date(func.timezone("Asia/Kolkata",Customers.created_at))
        deleted_at=func.date(func.timezone("Asia/Kolkata",Customers.deleted_at))
        cols=[*self.customer_cols]
        if include_deleted:
            cols.extend([Users.name.label('deleted_by'),deleted_at.label('deleted_at')])
        queried_customers=(await self.session.execute(
            select(
                *cols,
                date_expr.label("customer_created_at")
            )
            .join(Users,Users.id==Customers.deleted_by,isouter=True)
            .where(
                or_(
                    Customers.id.ilike(search_term),
                    Customers.name.ilike(search_term),
                    Customers.email.ilike(search_term),
                    Customers.industry.ilike(search_term),
                    func.cast(Customers.created_at,String).ilike(search_term),
                    Customers.website_url.ilike(search_term),
                    Customers.mobile_number.ilike(search_term),
                    Customers.sector.ilike(search_term),
                    Customers.gst_number.ilike(search_term),
                    Customers.owner.ilike(search_term),
                    Customers.tenant_id.ilike(search_term)
                ),
                Customers.sequence_id>cursor,
                Customers.is_deleted==include_deleted
            ).limit(limit).order_by(Customers.sequence_id.asc())
        )).mappings().all()

        total_customers:int=0
        if cursor==1:
            total_customers=(await self.session.execute(
                select(func.count(Customers.id)).where(Customers.is_deleted==False)
            )).scalar_one_or_none()

        return {
            'customers':queried_customers,
            'total_customers':total_customers,
            'total_pages':ceil(total_customers/limit),
            'next_cursor':queried_customers[-1]['sequence_id'] if len(queried_customers)>1 else None
        }
        
    
    async def search(self,query:str):
        search_term=f"%{query.lower()}%"
        queried_customers=(await self.session.execute(
            select(
                Customers.id,
                Customers.name,
            ).where(
                or_(
                    Customers.id.ilike(search_term),
                    Customers.name.ilike(search_term),
                    Customers.email.ilike(search_term),
                    Customers.industry.ilike(search_term),
                    func.cast(Customers.created_at,String).ilike(search_term),
                    Customers.website_url.ilike(search_term),
                    Customers.mobile_number.ilike(search_term),
                    Customers.sector.ilike(search_term),
                    Customers.gst_number.ilike(search_term),
                    Customers.owner.ilike(search_term),
                    Customers.tenant_id.ilike(search_term)
                ),
                Customers.is_deleted==False
            )
            .limit(5)
        )).mappings().all()

        return {'customers':queried_customers}

       
    async def get_by_id(self,customer_id:str):
        date_expr=func.date(func.timezone("Asia/Kolkata",Customers.created_at))
        queried_customers=(await self.session.execute(
            select(
                *self.customer_cols,
                date_expr.label("customer_created_at")
            )
            .where(Customers.id==customer_id,Customers.is_deleted==False)
        )).mappings().one_or_none()
        
        return {'customer':queried_customers}



