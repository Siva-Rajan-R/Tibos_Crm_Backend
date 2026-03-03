from . import BaseServiceModel
from ..models.order import Orders,OrdersPaymentInvoiceInfo
from ..models.product import Products
from ..models.customer import Customers
from ..repos.product_repo import ProductsRepo
from ..repos.customer_repo import CustomersRepo
from ..repos.distri_repo import DistributorsRepo
from core.utils.uuid_generator import generate_uuid
from ..repos.order_repo import OrdersRepo
from sqlalchemy import select,delete,update,or_,func,String
from sqlalchemy.ext.asyncio import AsyncSession
from icecream import ic
from core.data_formats.enums.user_enums import UserRoles
from core.data_formats.enums.order_enums import PurchaseTypes
from core.data_formats.typed_dicts.order_typdict import DeliveryInfo
from schemas.db_schemas.order import AddOrderDbSchema,UpdateOrderDbSchema
from schemas.request_schemas.order import AddOrderSchema,UpdateOrderSchema
from core.decorators.error_handler_dec import catch_errors
from math import ceil
from typing import Optional,List
from decimal import Decimal, ROUND_HALF_UP
from models.response_models.req_res_models import SuccessResponseTypDict,BaseResponseTypDict,ErrorResponseTypDict
from ..models.ui_id import TablesUiLId
from core.utils.ui_id_generator import generate_ui_id
from core.constants import UI_ID_STARTING_DIGIT,LUI_ID_ORDER_PREFIX
from core.utils.discount_validator import parse_discount,validate_discount
from core.data_formats.enums.order_enums import RenewalTypes
from core.utils.calculations import get_customer_price

import pandas as pd
from schemas.request_schemas.order import OrderFilterSchema
from core.utils.calculations import get_distributor_price,get_remaining_days
from core.data_formats.typed_dicts.order_typdict import DeliveryInfo,StatusInfo,LogisticsInfo
import json
from datetime import datetime
from pathlib import Path


def normalize_percent(value) -> Decimal:
    """
    Accepts:
      - '0.044'
      - '4.4%'
      - 0.044
      - 4.4
    Returns:
      Decimal('4.40')
    """
    if value is None:
        return None

    value = str(value).strip()

    if value.endswith('%'):
        return Decimal(value.replace('%', '')).quantize(Decimal('0.01'))

    d = Decimal(value)

    # if <= 1 assume fraction (0.044 → 4.4)
    if d <= 1:
        d = d * 100

    return d.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

def make_json_safe(obj):
    if isinstance(obj, dict):
        return {k: make_json_safe(v) for k, v in obj.items()}

    if isinstance(obj, (list, tuple, set)):
        return [make_json_safe(v) for v in obj]

    if hasattr(obj, "model_dump"):
        return make_json_safe(obj.model_dump())

    from datetime import datetime, date
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()

    try:
        import pandas as pd
        if isinstance(obj, pd.Timestamp):
            return obj.isoformat()
    except Exception:
        pass

    return str(obj)


def write_skipped_items_to_txt(skipped_items: list, prefix="skipped_orders"):
    if not skipped_items:
        return None

    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    output_dir = Path("skipped_reports")
    output_dir.mkdir(exist_ok=True)

    file_path = output_dir / f"{prefix}_{ts}.txt"

    with open(file_path, "w", encoding="utf-8") as f:
        for idx, item in enumerate(skipped_items, start=1):
            f.write(f"--- Skipped Item {idx} ---\n")
            safe_item = make_json_safe(item)
            f.write(json.dumps(safe_item, indent=2))
            f.write("\n\n")

    return str(file_path)

def safe_date(value, fmt="%Y-%m-%d"):
    if value is None:
        return None

    if isinstance(value, str):
        value = value.strip()
        if value == "":
            return None

    try:
        ts = pd.to_datetime(value, errors="coerce")
        if pd.isna(ts):
            return None
        return ts.strftime(fmt)
    except Exception:
        return None
    
def get_best_discount_id(discounts, distributor_type, product_price, quantity):
    order_amount = product_price * quantity

    # filter discounts by rebate type and threshold
    valid_discounts = [
        d for d in discounts
        if d["rebate_type"] == distributor_type
        and order_amount >= d["minimum_thershold"]
    ]

    if not valid_discounts:
        return None  # no applicable discount

    # pick the discount with highest minimum_threshold
    best_discount = max(
        valid_discounts,
        key=lambda d: d["minimum_thershold"]
    )

    return best_discount["id"]

class OrdersService(BaseServiceModel):
    def __init__(self,session:AsyncSession,user_role:UserRoles,cur_user_id:str):
        self.session=session
        self.user_role=user_role
        self.cur_user_id=cur_user_id


    @catch_errors
    async def add(self,data:AddOrderSchema):
        # need to check if the customer and the product is exists on the order
        # then check customer is exists or not
        # then chck product is exists or not
        order_obj=OrdersRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id)
        
        cust_exists=await CustomersRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).get_by_id(customer_id=data.customer_id)
        if not cust_exists or len(cust_exists)<1:
            return ErrorResponseTypDict(status_code=400,success=False,msg="Error : Adding Order",description="Customer with the given id does not exist")
        
        prod_exists=await ProductsRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).get_by_id(product_id=data.product_id)
        if not prod_exists or len(prod_exists)<1:
            return ErrorResponseTypDict(status_code=400,success=False,msg="Error : Adding Order",description="Product with the given id does not exist")
        
        distri_exists=await DistributorsRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).get_by_id(distributor_id=data.distributor_id)
        if not distri_exists or len(distri_exists)<1:
            return ErrorResponseTypDict(status_code=400,success=False,msg="Error : Adding Order",description="Distributor with the given id does not exist")

        data_toadd=data.model_dump(mode='json')

        order_id:str=generate_uuid()

        lui_id:str=(await self.session.execute(select(TablesUiLId.order_luiid))).scalar_one_or_none()
        cur_uiid=generate_ui_id(prefix=LUI_ID_ORDER_PREFIX,last_id=lui_id)
        return await order_obj.add(data=AddOrderDbSchema(**data_toadd,id=order_id,ui_id=cur_uiid))
    
    @catch_errors
    async def add_bulk(self,datas:List[dict]):
        skipped_items=[]
        datas_toadd=[]
        status_infotoadd=[]

        orders_obj=OrdersRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id)
        lui_id:str=(await self.session.execute(select(TablesUiLId.order_luiid))).scalar_one_or_none()

        for data in datas:
            
            cust_exists=await CustomersRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).get_by_id(customer_id=data['customer_id'])
            if not cust_exists['customer'] or len(cust_exists['customer'])<1:
                skipped_items.append(data)
                continue
            
            prod_exists=await ProductsRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).get_by_id(product_id=data['product_id'])
            if not prod_exists['product'] or len(prod_exists['product'])<1:
                skipped_items.append(data)
                continue
            
            distri_exists=await DistributorsRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).get_by_id(distributor_id=data['distributor_id'])
            if not distri_exists['distributors'] or len(distri_exists['distributors'])<1:
                skipped_items.append(data)
                continue
            # ic("Hii da mapla")
            ic(distri_exists['distributors']['discounts'],distri_exists['distributors']['discounts'].values(),data['distributor_type'].upper(),prod_exists['product']['price'],data['quantity'])
            discounts:dict=distri_exists['distributors']['discounts']
            # ic(discounts)
            discount_id=None
            converted_discounts=[]
            existing_discounts=[]
            
            converted_discount_val = normalize_percent(data['distributor_discount'])
            for discount in discounts.values():
                existing_discount_val = normalize_percent(discount['discount'])
                
                converted_discounts.append(f"{converted_discount_val}%")
                existing_discounts.append(f"{existing_discount_val}%")

                ic(converted_discount_val, existing_discount_val)

                if (
                    discount['rebate_type'].upper() == data['distributor_type'].upper()
                    and converted_discount_val == existing_discount_val
                ):
                    discount_id = discount['id']
                    break
            data['converted_discounts']=converted_discounts
            data['existing_discounts']=existing_discounts
            if discount_id is None:
                skipped_items.append(data)
                continue

            data['discount_id']=discount_id
            data['customer_id']=cust_exists['customer']['id']
            data['distributor_id']=distri_exists['distributors']['id']
            data['product_id']=prod_exists['product']['id']

            data['vendor_commision']=str(data['vendor_commision'])
            
            data['delivery_info']=DeliveryInfo(
                requested_date=safe_date(data['requested_date']),
                delivery_date=safe_date(data['delivery_date']),
                shipping_method=data['shipping_method'],
                payment_terms=data['payment_terms']
            )


            data['status_info']=StatusInfo(
                payment_status=data['payment_status'],
                invoice_status=data['invoice_status'],
            )
            invoice_number = data.get("invoice_number")
            if pd.isna(invoice_number) or invoice_number == "":
                invoice_number = None
            else:
                invoice_number = str(invoice_number)
            if invoice_number:
                data['status_info']['invoice_number']=invoice_number
            
            invoice_date=safe_date(data['invoice_date'])
            if invoice_date:
                data['status_info']['invoice_date']=invoice_date
            
            paid_amount=get_customer_price(customer_price=data['unit_price'],qty=data['quantity']).get('with_gst')
            ic(paid_amount)
            data['status_info']['paid_amount']=int(paid_amount)

            data['logistic_info']=LogisticsInfo(
                purchase_type=data['purchase_type'],
                renewal_type=data['renewal_type'],
                bill_to=data['bill_to'],
                distributor_type=data['distributor_type']
            )

            
            
            data['additional_discount']=str(data['discount'])
            order_id:str=generate_uuid()
            cur_uiid=generate_ui_id(prefix=LUI_ID_ORDER_PREFIX,last_id=lui_id)
            lui_id=cur_uiid
            del data['existing_discounts']
            del data['converted_discounts']

            status_infotoadd.append(OrdersPaymentInvoiceInfo(**data['status_info'],order_id=order_id))
            data['status_info']=[data['status_info']]
            formatted_schema=AddOrderDbSchema(**data,id=order_id,ui_id=cur_uiid).model_dump(mode='json',exclude_unset=True,exclude_none=True,exclude=['status_info'])
            ic(data['logistic_info']['renewal_type'])
            if data['logistic_info']['renewal_type']==RenewalTypes.YEARLY_YEARLY_BILL.value:
                datas_toadd.append(Orders(**formatted_schema))


        skipped_file_path = write_skipped_items_to_txt(skipped_items)

        ic("skipped_items_count", len(skipped_items))
        ic("orders_to_insert_count", len(datas_toadd))
        ic("Skipped file path",skipped_file_path)
        return await orders_obj.add_bulk(datas=datas_toadd,lui_id=lui_id,status_datas=status_infotoadd)
    

    @catch_errors
    async def update(self,data:UpdateOrderSchema):
        data_toupdate=data.model_dump(mode='json',exclude_none=True,exclude_unset=True)
        if not data_toupdate or len(data_toupdate)<1:
            return ErrorResponseTypDict(status_code=400,success=False,msg="Error : Updating Order",description="No valid fields to update provided")
        
        order_obj=OrdersRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id)

        cust_exists=await CustomersRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).get_by_id(customer_id=data.customer_id)
        if not cust_exists or len(cust_exists)<1:
            return ErrorResponseTypDict(status_code=400,success=False,msg="Error : Adding Order",description="Customer with the given id does not exist")
        
        prod_exists=await ProductsRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).get_by_id(product_id=data.product_id)
        if not prod_exists or len(prod_exists)<1:
            return ErrorResponseTypDict(status_code=400,success=False,msg="Error : Adding Order",description="Product with the given id does not exist")
        
        distri_exists=await DistributorsRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).get_by_id(distributor_id=data.distributor_id)
        if not distri_exists or len(distri_exists)<1:
            return ErrorResponseTypDict(status_code=400,success=False,msg="Error : Adding Order",description="Distributor with the given id does not exist")


        return await OrdersRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).update(data=UpdateOrderDbSchema(**data_toupdate))


    @catch_errors    
    async def delete(self,order_id:str,customer_id:str,soft_delete:bool=True):
        return await OrdersRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).delete(order_id=order_id,customer_id=customer_id,soft_delete=soft_delete)
    
    @catch_errors  
    async def recover(self,order_id:str,customer_id:str):
        return await OrdersRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).recover(order_id=order_id,customer_id=customer_id)

    @catch_errors
    async def get(self,filter:OrderFilterSchema,cursor:int=1,limit:int=10,query:str='',include_deleted:Optional[bool]=False,):
        return await OrdersRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).get(cursor=cursor,limit=limit,query=query,include_deleted=include_deleted,filter=filter)
    
    @catch_errors
    async def search(self,query:str):
        return await OrdersRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).search(query=query)

    @catch_errors  
    async def get_by_id(self,order_id:str):
        return await OrdersRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).get_by_id(order_id=order_id)
        
    @catch_errors
    async def get_by_customer_id(self,customer_id:str,cursor:int,limit:int):
        return await OrdersRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).get_by_customer_id(customer_id=customer_id,cursor=cursor,limit=limit)
    
    @catch_errors
    async def get_last_order(self,customer_id:str,product_id:str):
        return await OrdersRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).get_last_order(customer_id=customer_id,product_id=product_id)



