from . import HTTPException,BaseRepoModel
from ..models.product import Products,ProductTypes
from ..models.order import Orders
from core.utils.uuid_generator import generate_uuid
from sqlalchemy import select,delete,update,or_,cast,String,func,Float
from sqlalchemy.ext.asyncio import AsyncSession
from icecream import ic
from core.data_formats.enums.common_enums import UserRoles
from core.decorators.db_session_handler_dec import start_db_transaction
from schemas.db_schemas.product import AddProductDbSchema,UpdateProductDbSchema
from math import ceil
from ..models.user import Users
from typing import List
from models.response_models.req_res_models import SuccessResponseTypDict,BaseResponseTypDict,ErrorResponseTypDict



class ProductsRepo(BaseRepoModel):
    def __init__(self,session:AsyncSession,user_role:UserRoles,cur_user_id:str):
        self.session=session
        self.user_role=user_role
        self.low_qty_thershold=5
        self.cur_user_id=cur_user_id
        self.products_cols=(
            Products.sequence_id,
            Products.id,
            Products.name,
            Products.description,
            Products.available_qty.label('quantity'),
            Products.price,
            Products.product_type,
            Products.part_number
        )

    async def get_by_part_number(self,part_number:str):
        queried_products=(await self.session.execute(
            select(Products.id)
            .where(Products.part_number==part_number,Products.is_deleted==False)
        )).scalar_one_or_none()
        return queried_products
    
    @start_db_transaction
    async def add(self,data:AddProductDbSchema):
        self.session.add(Products(**data.model_dump(mode='json')))
        return True
    
    @start_db_transaction
    async def add_bulk(self,datas:List[Products]):
        self.session.add_all(datas)
        return True


    @start_db_transaction   
    async def update(self,data:UpdateProductDbSchema):
        data_toupdate=data.model_dump(mode='json',exclude=['product_id'],exclude_none=True,exclude_unset=True)
        if not data_toupdate or len(data_toupdate)<1:
            return ErrorResponseTypDict(status_code=400,success=False,msg="Error : Updating Product",description="No valid fields to update provided")
        
        prod_toupdate=update(Products).where(Products.id==data.product_id).values(
            **data_toupdate
        ).returning(Products.id)

        is_updated=(await self.session.execute(prod_toupdate)).scalar_one_or_none()
        
        return is_updated if is_updated else ErrorResponseTypDict(status_code=400,success=False,msg="Error : Updating Product",description="Unable to update the product, may be invalid product id or no changes in data")

    @start_db_transaction
    async def delete(self,product_id:str,soft_delete:bool=True):
        have_order=(await self.session.execute(select(Orders.id).where(Orders.product_id==product_id,Orders.is_deleted==False).limit(1))).scalar_one_or_none()
        if have_order:
            return ErrorResponseTypDict(status_code=400,success=False,msg="Error : Deleting Product",description="Unable to delete the product, as there are existing orders associated with this product")

        if soft_delete:
            prod_todelete=update(Products).where(Products.id==product_id,Products.is_deleted==False).values(
                is_deleted=True,
                deleted_at=func.now(),
                deleted_by=self.cur_user_id
            ).returning(Products.id)

            is_deleted=(await self.session.execute(prod_todelete)).scalar_one_or_none()
            

        else:
            if self.user_role if isinstance(self.user_role,UserRoles) else self.user_role!=UserRoles.SUPER_ADMIN.value:
                return ErrorResponseTypDict(status_code=403,success=False,msg="Error : Deleting Product",description="Only super admin can perform hard delete operation")
            
            prod_todelete=delete(Products).where(Products.id==product_id).returning(Products.id)
            is_deleted=(await self.session.execute(prod_todelete)).scalar_one_or_none()
        return is_deleted if is_deleted else ErrorResponseTypDict(status_code=400,success=False,msg="Error : Deleting Product",description="Unable to delete the product, may be invalid product id or product already deleted")
    
    @start_db_transaction
    async def recover(self,product_torecover:str):
        if self.user_role if isinstance(self.user_role,UserRoles) else self.user_role!=UserRoles.SUPER_ADMIN.value:
            return ErrorResponseTypDict(status_code=403,success=False,msg="Error : Recovering Product",description="Only super admin can perform recover operation")

        prod_torecover=update(Products).where(Products.id==product_torecover,Products.is_deleted==True).values(
            is_deleted=False
        ).returning(Products.id)
        is_recovered=(await self.session.execute(prod_torecover)).scalar_one_or_none()
        return is_recovered if is_recovered else ErrorResponseTypDict(status_code=400,success=False,msg="Error : Recovering Product",description="Unable to recover the product, may product is not deleted or already recovered")
        
    async def get(self,cursor:int=1,limit:int=10,query:str='',include_deleted:bool=False):
        search_term=f"%{query.lower()}%"
        date_expr=func.date(func.timezone("Asia/Kolkata",Products.created_at))
        deleted_at=func.date(func.timezone("Asia/Kolkata",Products.deleted_at))
        cols=[*self.products_cols]
        if include_deleted:
            cols.extend([Users.name.label('deleted_by'),deleted_at.label('deleted_at')])

        queried_products=(await self.session.execute(
            select(
                *cols,
                date_expr.label("product_created_at")
            )
            .join(Users,Users.id==Products.deleted_by,isouter=True)
            .where(
                or_(
                    Products.id.ilike(search_term),
                    Products.name.ilike(search_term),
                    Products.description.ilike(search_term),
                    Products.product_type.ilike(search_term),
                    func.cast(Products.created_at,String).ilike(search_term)
                ),
                Products.sequence_id>cursor,
                Products.is_deleted==include_deleted

            )
            .limit(limit)
            .order_by(Products.name)
        )).mappings().all()

        total_products:int=0
        low_qty:int=0
        if cursor == 1:
            total_products=(await self.session.execute(
                select(func.count(Products.id)).where(Products.is_deleted==False)
            )).scalar_one_or_none()

            low_qty=(await self.session.execute(
                select(func.count()).select_from(Products).where(Products.available_qty<=self.low_qty_thershold,Products.is_deleted==False)
            )).scalar()

        return {
            'products':queried_products,
            'total_products':total_products,
            'total_pages':ceil(total_products/limit),
            'low_quantites':low_qty,
            'next_cursor':queried_products[-1]["sequence_id"] if len(queried_products)>1 else None
        }
    

    async def search(self, query: str):
        search_term = f"%{query.lower()}%"

        result = await self.session.execute(
            select(
                Products.id,
                Products.name,
                Products.price.label("price"),
                
            )
            .where(
                or_(
                    Products.id.ilike(search_term),
                    Products.name.ilike(search_term),
                    Products.description.ilike(search_term),
                    Products.product_type.ilike(search_term),
                ),
                Products.is_deleted==False
            )
            .order_by(Products.name)
            .limit(5)
        )

        products = result.mappings().all()
        ic(products)
        return {"products": products}
        
    async def get_by_id(self,product_id:str):
        date_expr=func.date(func.timezone("Asia/Kolkata",Products.created_at))
        queried_products=(await self.session.execute(
            select(
                *self.products_cols,
                date_expr.label("product_created_at")
            )
            .where(or_(Products.id==product_id,Products.part_number==product_id),Products.is_deleted==False)
            .order_by(Products.name)
        )).mappings().one_or_none()

        return {'product':queried_products}



