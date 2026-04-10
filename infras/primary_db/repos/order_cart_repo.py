from typing import cast,List
from . import HTTPException,BaseRepoModel
from ..models.order import CartOrders,OrdersPaymentInvoiceInfo,CartOrdersProduct,CartOrdersPaymentInvoiceInfo
from ..models.product import Products
from ..models.customer import Customers
from ..models.distributor import Distributors
from core.utils.uuid_generator import generate_uuid
from sqlalchemy import Numeric, select,delete,update,or_,func,String,cast,case,and_,Date,desc,text,exists
from sqlalchemy.ext.asyncio import AsyncSession
from icecream import ic
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import literal,true
from core.data_formats.enums.user_enums import UserRoles
from core.data_formats.enums.order_enums import PaymentStatus,InvoiceStatus,PurchaseTypes,OrderFilterRevenueEnum,ActivationStatusEnum
from schemas.db_schemas.order import AddCartOrderDbSchema,UpdateCartOrderProductDbSchema,UpdateCartOrderDbSchema,AddCartOrderProductDbSchema
from core.decorators.db_session_handler_dec import start_db_transaction
from math import ceil
from ..models.user import Users
from models.response_models.req_res_models import SuccessResponseTypDict,BaseResponseTypDict,ErrorResponseTypDict
from core.utils.discount_validator import validate_discount
from ..models.ui_id import TablesUiLId
from schemas.request_schemas.order import OrderFilterSchema
from datetime import datetime,timedelta
from core.constants import DEFAULT_ADDON_YEAR
from typing import Optional,Literal
from core.data_formats.enums.order_enums import OrderFilterDateByEnum
from ..calculations import distri_final_price,customer_final_price,profit_loss_price,customer_tot_price,distributor_tot_price,vendor_disc_price,distri_additi_price,distri_disc_price,remaining_days,last_order_delivery_date,expiry_date,distri_discount,pending_amount,total_paid_amount,customer_amount_with_gst



class OrdersCartRepo(BaseRepoModel):
    def __init__(self,session:AsyncSession,user_role:UserRoles,cur_user_id:str):
        self.session=session
        self.user_role=user_role
        self.cur_user_id=cur_user_id
        self.product_subquery=(
            select(
                CartOrdersProduct.order_id,
                func.json_agg(
                    func.json_build_object(
                        "id",CartOrdersProduct.id,
                        "product_id", CartOrdersProduct.product_id,
                        "additional_discount", CartOrdersProduct.additional_discount,
                        "additional_price", CartOrdersProduct.additional_price,
                        "unit_price", CartOrdersProduct.unit_price,
                        "discount_id", CartOrdersProduct.discount_id,
                        "discount" , Distributors.discounts[CartOrdersProduct.discount_id],
                        "vendor_commision", CartOrdersProduct.vendor_commision,
                        "quantity", CartOrdersProduct.quantity,
                        "name", Products.name,
                        "price", Products.price,
                    )
                ).label("products")
            )
            .join(CartOrders, CartOrders.id == CartOrdersProduct.order_id)
            .join(Distributors,Distributors.id==CartOrders.distributor_id)
            .join(Products, Products.id == CartOrdersProduct.product_id)
            .group_by(CartOrdersProduct.order_id)  # Only group in the subquery
        ).subquery()

        self.orders_cols=(
            CartOrders.id,
            CartOrders.ui_id,
            CartOrders.logistic_info,
            CartOrders.delivery_info,
            Customers.name,
            Customers.email,
            CartOrders.distributor_id,
            Distributors.name.label("distributor_name"),
            self.product_subquery.c.products

        )


    @start_db_transaction
    async def add(self,order_data:AddCartOrderDbSchema,product_datas:List[CartOrdersProduct]):
        self.session.add(CartOrders(**order_data.model_dump(mode='json',exclude=['lui_id','status_info','products'])))
        self.session.add_all(product_datas)
        invoicetoadd=order_data.model_dump(mode='json')

        invoicetoadd_bulk=[]
        for status in invoicetoadd['status_info']:
            invoicetoadd_bulk.append(CartOrdersPaymentInvoiceInfo(**status,order_id=order_data.id))
        
        self.session.add_all(invoicetoadd_bulk)
        await self.session.execute(update(TablesUiLId).where(TablesUiLId.id=="1").values(cart_order_luiid=order_data.ui_id))
        # need to implement invoice generation process + email sending
        return True

    
    @start_db_transaction
    async def update(self,order_data:UpdateCartOrderDbSchema,products_data:List[dict]):
        data_toupdate=order_data.model_dump(mode='json',exclude=['product_id','customer_id','order_id','status_info','products'],exclude_none=True,exclude_unset=True)
        if not data_toupdate or len(data_toupdate)<1:
            return ErrorResponseTypDict(status_code=400,success=False,msg="Error : Updating Order",description="No valid fields to update provided")
        
        invoicetoadd=order_data.model_dump(mode='json')
        invoicetoadd_bulk=[]
        await self.session.execute(delete(CartOrdersPaymentInvoiceInfo).where(CartOrdersPaymentInvoiceInfo.order_id==order_data.order_id))
        for status in invoicetoadd['status_info']:
            invoicetoadd_bulk.append(CartOrdersPaymentInvoiceInfo(**status,order_id=order_data.order_id))
        self.session.add_all(invoicetoadd_bulk)


        await self.session.run_sync(
            lambda s: s.bulk_update_mappings(CartOrdersProduct,products_data)
        )


        cart_order_toupdate=update(CartOrders).where(CartOrders.id==order_data.order_id).values(
            **data_toupdate
        ).returning(CartOrders.id)

        is_updated=(await self.session.execute(cart_order_toupdate)).scalar_one_or_none()
        
        # need to implement invoice generation process + email sending
        return is_updated if is_updated else ErrorResponseTypDict(status_code=400,success=False,msg="Error : Updating Order",description="Unable to update the order, may be invalid order id or no changes in data")

    @start_db_transaction    
    async def delete(self,order_id:str,soft_delete:bool=True):
        ic(soft_delete)
        if soft_delete:
            cart_order_todelete=update(CartOrders).where(CartOrders.id==order_id,CartOrders.is_deleted==False).values(
                is_deleted=True,
                deleted_at=func.now(),
                deleted_by=self.cur_user_id
            ).returning(CartOrders.id)

            is_deleted=(await self.session.execute(cart_order_todelete)).scalar_one_or_none()

        else:
            if self.user_role if isinstance(self.user_role,UserRoles) else self.user_role!=UserRoles.SUPER_ADMIN.value:
                return ErrorResponseTypDict(status_code=403,success=False,msg="Error : Deleting Order",description="Only super admin can perform hard delete operation")
            
            cart_order_todelete=delete(CartOrders).where(CartOrders.id==order_id).returning(CartOrders.id)
            is_deleted=(await self.session.execute(cart_order_todelete)).scalar_one_or_none()
            
            # need to implement email sending "Your orders has been stoped from CRM"
        return is_deleted if is_deleted else ErrorResponseTypDict(status_code=400,success=False,msg="Error : Deleting Order",description="Unable to delete the order, may be invalid order id or order already deleted")
    

    async def get_by_id(self,order_id:str):
        stmt=(
            select(
                *self.orders_cols
            )
            .where(
                CartOrders.id==order_id,
                CartOrders.is_deleted==False
            )
            .join(Distributors,Distributors.id==CartOrders.distributor_id,isouter=True)
            .join(Customers, Customers.id == CartOrders.customer_id, isouter=True)
            .join(self.product_subquery, self.product_subquery.c.order_id == CartOrders.id, isouter=True)
        )

        results=(await self.session.execute(stmt)).mappings().one_or_none()
        ic(results)
        return results



        
    async def get(
        self,
        filter: Optional[OrderFilterSchema]=OrderFilterSchema(),
        cursor: int = 1,
        limit: int = 10,
        query: str = '',
        include_deleted: bool = False,
        in_search:List=[]
    ):
        

        stmt = (
            select(
                *self.orders_cols
            )
            .where(
                
            )
            .join(Distributors,Distributors.id==CartOrders.distributor_id,isouter=True)
            .join(Customers, Customers.id == CartOrders.customer_id, isouter=True)
            .join(self.product_subquery, self.product_subquery.c.order_id == CartOrders.id, isouter=True)
            .limit(limit)
            .offset(cursor)
        )

        results=(await self.session.execute(stmt)).mappings().all()

        ic(results)

        return results
    
    async def search(self,query:str):
        ...

    




