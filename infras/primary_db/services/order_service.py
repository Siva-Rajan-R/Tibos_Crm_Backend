from . import BaseServiceModel
from ..models.order import Orders,OrdersPaymentInvoiceInfo
from ..models.product import Products
from ..models.customer import Customers
from ..repos.product_repo import ProductsRepo
from ..repos.user_repo import UserRepo
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
from schemas.db_schemas.order import AddOrderDbSchema,UpdateOrderDbSchema,OrderBulkDeleteDbSchema
from schemas.request_schemas.order import AddOrderSchema,UpdateOrderSchema,OrderBulkDeleteSchema
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
from core.utils.msblob import generate_sas_url,upload_excel_to_blob
from services.sse import sse_manager,sse_msg_builder
import pandas as pd
from schemas.request_schemas.order import OrderFilterSchema
from core.utils.calculations import get_distributor_price,get_remaining_days,get_customer_addon_price
from core.data_formats.typed_dicts.order_typdict import DeliveryInfo,StatusInfo,LogisticsInfo,InvoiceStatus,PaymentStatus,PurchaseTypes
import json
from datetime import datetime
from pathlib import Path
from services.email_service import send_email


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


def write_skipped_items_to_excel(skipped_items: list, prefix="skipped_orders"):
    if not skipped_items:
        return None

    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

    output_dir = Path("skipped_reports")
    output_dir.mkdir(exist_ok=True)

    file_path = output_dir / f"{prefix}_{ts}.xlsx"

    # convert nested objects safely
    safe_items = [make_json_safe(item) for item in skipped_items]

    df = pd.DataFrame(safe_items)

    df.to_excel(file_path, index=False)

    return file_path.as_posix()

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
        if not cust_exists['customer'] or len(cust_exists['customer'])<1:
            return ErrorResponseTypDict(status_code=400,success=False,msg="Error : Adding Order",description="Customer with the given id does not exist")
        
        prod_exists=await ProductsRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).get_by_id(product_id=data.product_id)
        if not prod_exists['product'] or len(prod_exists['product'])<1:
            return ErrorResponseTypDict(status_code=400,success=False,msg="Error : Adding Order",description="Product with the given id does not exist")
        
        ic(prod_exists['product']['price']>0,data.additional_price!=None)
        if prod_exists['product']['price']>0 and (data.additional_price!=None and data.additional_price!=0):
            return ErrorResponseTypDict(status_code=400,success=False,msg="Error : Adding Order",description="Product have a price you cantbe able to add addtional price")
        
        distri_exists=await DistributorsRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).get_by_id(distributor_id=data.distributor_id)
        if not distri_exists['distributors'] or len(distri_exists['distributors'])<1:
            return ErrorResponseTypDict(status_code=400,success=False,msg="Error : Adding Order",description="Distributor with the given id does not exist")

        data_toadd=data.model_dump(mode='json')

        order_id:str=generate_uuid()

        lui_id:str=(await self.session.execute(select(TablesUiLId.order_luiid))).scalar_one_or_none()
        cur_uiid=generate_ui_id(prefix=LUI_ID_ORDER_PREFIX,last_id=lui_id)
        return await order_obj.add(data=AddOrderDbSchema(**data_toadd,id=order_id,ui_id=cur_uiid))
    
    # @catch_errors
    async def add_bulk(self,datas:List[dict]):
        skipped_items=[]
        datas_toadd=[]
        status_infotoadd=[]

        orders_obj=OrdersRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id)
        lui_id:str=(await self.session.execute(select(TablesUiLId.order_luiid))).scalar_one_or_none()

        for data in datas:
            
            cust_exists=await CustomersRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).get_by_id(customer_id=data['customer_id'])
            if not cust_exists['customer'] or len(cust_exists['customer'])<1:
                data['reason']="Customer id not Found"
                skipped_items.append(data)
                continue
            
            prod_exists=await ProductsRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).get_by_id(product_id=data['product_id'])
            if not prod_exists['product'] or len(prod_exists['product'])<1:
                data['reason']="Product id not found"
                skipped_items.append(data)
                continue
            
            distri_exists=await DistributorsRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).get_by_id(distributor_id=data['distributor_id'])
            if not distri_exists['distributors'] or len(distri_exists['distributors'])<1:
                data['reason']="Distributor Not Found"
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
                data['reason']="Discount or Rebate Type Mistmatched"
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
            
            paid_amount=0
            ic(data['status_info'])
            if  data['status_info']['invoice_status']==InvoiceStatus.COMPLETED.value and data['status_info']['payment_status']==PaymentStatus.FULL_PAYMENT_RECEIVED.value:
                if data['purchase_type']==PurchaseTypes.EXISTING_ADD_ON.value:
                    last_order=(await orders_obj.get_last_order(customer_id=data['customer_id'],product_id=data['product_id']))
                    if not last_order['last_order'] or len(last_order['last_order'])<1:
                        data['reason']="This customer+Product doesn't have on order"
                        skipped_items.append(data)
                        continue

                    expiry_date=last_order['last_order']['expiry_date']
                    remaining_days=get_remaining_days(from_date=expiry_date,to_date=data['delivery_info']['delivery_date'])
                    if remaining_days>365:
                        data['last_order']=last_order
                        data['remaing_days']=remaining_days
                        data['reason']="Date excedding >365"
                        skipped_items.append(data)
                        continue
                    
                    data['unit_price']=last_order['last_order']['unit_price']
                    paid_amount=get_customer_addon_price(customer_price=data['unit_price'],qty=data['quantity'],expiry_date=expiry_date,delivery_date=data['delivery_info']['delivery_date']).get("with_gst")
                
                else:
                    paid_amount=get_customer_price(customer_price=data['unit_price'],qty=data['quantity']).get('with_gst')
                    ic(paid_amount)
            
            if data['purchase_type']==PurchaseTypes.EXISTING_ADD_ON.value:
                last_order=(await orders_obj.get_last_order(customer_id=data['customer_id'],product_id=data['product_id']))
                if not last_order['last_order'] or len(last_order['last_order'])<1:
                    data['reason']="This customer+Product doesn't have on order"
                    skipped_items.append(data)
                    continue
                else:   
                    last_order=(await orders_obj.get_last_order(customer_id=data['customer_id'],product_id=data['product_id']))
                    data['unit_price']=last_order['last_order']['unit_price']
                    paid_amount=0

            data['status_info']['paid_amount']=round(paid_amount)
            data['activated']=False

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

            
            
            ic(data['logistic_info']['renewal_type'])
            if data['logistic_info']['renewal_type']==RenewalTypes.YEARLY_YEARLY_BILL.value or data['logistic_info']['renewal_type']==RenewalTypes.MONTHLY_BILL_MONTHLY_COMMITMENT.value:
                status_infotoadd.append(OrdersPaymentInvoiceInfo(**data['status_info'],order_id=order_id))
                data['status_info']=[data['status_info']]
                formatted_schema=AddOrderDbSchema(**data,id=order_id,ui_id=cur_uiid).model_dump(mode='json',exclude_unset=True,exclude_none=True,exclude=['status_info'])
                datas_toadd.append(Orders(**formatted_schema))
            else:
                data['reason']="YEARLY_YEARLY_BILL and MONTHLY_BILL_MONTHLY_COMMITMENT only Allowed"
                skipped_items.append(data)


        skipped_file_path = write_skipped_items_to_excel(skipped_items)

        ic("skipped_items_count", len(skipped_items))
        ic("orders_to_insert_count", len(datas_toadd))
        ic("Skipped file path",skipped_file_path)
        if skipped_file_path:
            blob_name=upload_excel_to_blob(local_file_path=skipped_file_path)
            url=generate_sas_url(blob_name=blob_name)
            ic(url)
            msg=sse_msg_builder(title="Skiped datas report",description="During bulk upload these are the datas are skipped",type="file",url=url)
            await sse_manager.send(self.cur_user_id,data=msg)
        else:
            user=await UserRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).get_by_id(userid_toget=self.cur_user_id)
            user_email=user['user']['email']

            await send_email(client_ip="",reciver_emails=[user_email],subject="Skiped datas report",body="During bulk upload these are the datas are skipped",is_html=False,sender_email_id="crm@tibos.in")

        return await orders_obj.add_bulk(datas=datas_toadd,lui_id=lui_id,status_datas=status_infotoadd)
    

    @catch_errors
    async def update(self,data:UpdateOrderSchema):
        data_toupdate=data.model_dump(mode='json',exclude_none=True,exclude_unset=True)
        if not data_toupdate or len(data_toupdate)<1:
            return ErrorResponseTypDict(status_code=400,success=False,msg="Error : Updating Order",description="No valid fields to update provided")
        
        order_obj=OrdersRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id)

        cust_exists=await CustomersRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).get_by_id(customer_id=data.customer_id)
        if not cust_exists['customer'] or len(cust_exists['customer'])<1:
            return ErrorResponseTypDict(status_code=400,success=False,msg="Error : Updaing Order",description="Customer with the given id does not exist")
        
        prod_exists=await ProductsRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).get_by_id(product_id=data.product_id)
        if not prod_exists['product'] or len(prod_exists['product'])<1:
            return ErrorResponseTypDict(status_code=400,success=False,msg="Error : Updaing Order",description="Product with the given id does not exist")
        
        if prod_exists['product']['price']>0 and (data.additional_price!=None and data.additional_price!=0):
            return ErrorResponseTypDict(status_code=400,success=False,msg="Error : Updaing Order",description="Product have a price you cantbe able to add addtional price")
        distri_exists=await DistributorsRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).get_by_id(distributor_id=data.distributor_id)

        if not distri_exists['distributors'] or len(distri_exists['distributors'])<1:
            return ErrorResponseTypDict(status_code=400,success=False,msg="Error : Updaing Order",description="Distributor with the given id does not exist")


        return await OrdersRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).update(data=UpdateOrderDbSchema(**data_toupdate))


    @catch_errors    
    async def delete(self,order_id:str,customer_id:str,soft_delete:bool=True):
        return await OrdersRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).delete(order_id=order_id,customer_id=customer_id,soft_delete=soft_delete)
    
    @catch_errors    
    async def delete_bulk(self,data:OrderBulkDeleteSchema,soft_delete:bool=True):
        data=OrderBulkDeleteDbSchema(order_ids=data.order_ids)
        return await OrdersRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).delete_bulk(data=data,soft_delete=soft_delete)
    
    @catch_errors  
    async def recover(self,order_id:str,customer_id:str):
        return await OrdersRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).recover(order_id=order_id,customer_id=customer_id)

    @catch_errors
    async def get(self,filter:OrderFilterSchema,cursor:int=1,limit:int=10,query:str='',include_deleted:Optional[bool]=False):
        ic("Inside get order service")
        return await OrdersRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).get(cursor=cursor,limit=limit,query=query,include_deleted=include_deleted,filter=filter)
    
    @catch_errors
    async def test(self,cursor:int=1,limit:int=10,query:str='',include_deleted:Optional[bool]=False):
        ic("Inside get order service")
        return await OrdersRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).test(cursor=cursor,limit=limit,query=query,include_deleted=include_deleted)
    
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



