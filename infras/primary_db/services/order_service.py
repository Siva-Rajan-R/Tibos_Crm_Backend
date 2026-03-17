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
from schemas.request_schemas.order import AddOrderSchema,UpdateOrderSchema,OrderBulkDeleteSchema,AddSearchField,UpdateSearchField
from core.decorators.error_handler_dec import catch_errors
from math import ceil
from typing import Optional,List
from decimal import Decimal, ROUND_HALF_UP
from models.response_models.req_res_models import SuccessResponseTypDict,BaseResponseTypDict,ErrorResponseTypDict
from ..models.ui_id import TablesUiLId
from core.utils.ui_id_generator import generate_ui_id
from core.constants import UI_ID_STARTING_DIGIT,LUI_ID_ORDER_PREFIX,DEFAULT_ADDON_YEAR
from core.utils.discount_validator import parse_discount,validate_discount
from core.data_formats.enums.order_enums import RenewalTypes
from core.utils.calculations import get_customer_price
from core.utils.msblob import generate_sas_url,upload_excel_to_blob
from services.sse import sse_manager,sse_msg_builder
import pandas as pd
from schemas.request_schemas.order import OrderFilterSchema
from core.utils.calculations import get_distributor_price,get_remaining_days,get_customer_addon_price
from core.data_formats.typed_dicts.order_typdict import DeliveryInfo,StatusInfo,LogisticsInfo,InvoiceStatus,PaymentStatus,PurchaseTypes,RenewalTypes
from core.data_formats.enums.order_enums import ActivationStatusEnum
import json
from datetime import datetime,timedelta
from pathlib import Path
from services.email_service import send_email
from ...search_engine.models.order import OrderSearch
from core.utils.percentage_convertor import normalize_percent
from core.utils.safe_date_convertor import safe_date
from core.utils.skipped_data_convertor import write_skipped_items_to_excel






    
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


    async def add(self,data:AddOrderSchema):
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

        if data.logistic_info.get("purchase_type")==PurchaseTypes.EXISTING_ADD_ON.value:
            last_order=(await order_obj.get_by_id(order_id=data.last_order_id))
            # last_order=(await orders_obj.get_last_order(customer_id=data['customer_id'],product_id=data['product_id']))
            if not last_order['order'] or len(last_order['order'])<1:
                return ErrorResponseTypDict(status_code=400,success=False,msg="Error : Adding Order",description="Invalid Last Order")
            ic(last_order)
            data_toadd['logistic_info']['last_order_id']=data.last_order_id            
            data_toadd['logistic_info']['last_ord_expiry_date']=last_order['order']['delivery_info']['delivery_date']

        search_fields=AddSearchField(
            ui_id=cur_uiid,
            id=order_id,
            distributor_id=data.distributor_id,
            customer_id=data.customer_id,
            product_id=data.product_id,
            distributor_name=distri_exists['distributors']['name'],
            distributor_ui_id=distri_exists['distributors']['ui_id'],
            product_name=prod_exists['product']['name'],
            product_type=prod_exists['product']['product_type'],
            product_ui_id=prod_exists['product']['ui_id'],
            customer_email=', '.join(cust_exists['customer']['emails']),
            customer_name=cust_exists['customer']['name'],
            customer_ui_id=cust_exists['customer']['ui_id'],
        ).model_dump(mode="json")

        # await OrderSearch().create_document(data=search_fields)
        return await order_obj.add(data=AddOrderDbSchema(**data_toadd,id=order_id,ui_id=cur_uiid))
    
    # @catch_errors
    async def add_bulk(self,datas:List[dict]):
        skipped_items=[]
        datas_toadd=[]
        status_infotoadd=[]
        searchable_data=[]

        renewal_types = [e.value for e in RenewalTypes]
        purchase_types = [e.value for e in PurchaseTypes]
        invoice_status = [e.value for e in InvoiceStatus]
        payment_status = [e.value for e in PaymentStatus]
        activation_satus=[e.value for e in ActivationStatusEnum]

        
            

        orders_obj=OrdersRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id)
        lui_id:str=(await self.session.execute(select(TablesUiLId.order_luiid))).scalar_one_or_none()

        for data in datas:
            ic(renewal_types)
            if data['renewal_type'] not in renewal_types:   
                data['reason']=f"Invalid Renewal Types, Renewal Types should be {renewal_types}"
                skipped_items.append(data)
                continue

            if data['purchase_type'] not in purchase_types:
                data['reason']=f"Invalid Purchase Types, Purchase Types should be {purchase_types}"
                skipped_items.append(data)
                continue

            if data['payment_status'] not in payment_status:
                data['reason']=f"Invalid Payment Status, Payment Status should be {payment_status}"
                skipped_items.append(data)
                continue

            if data['invoice_status'] not in invoice_status:
                data['reason']=f"Invalid Invoice Status, Invoice Status should be {invoice_status}"
                skipped_items.append(data)
                continue

            if data['activated'] not in activation_satus:
                data['reason']=f"Invalid Activation Status, Activation Status should be {activation_satus}"
                skipped_items.append(data)
                continue

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
                
            is_activated=False
            ic(data['activated'])
            if data['activated']==ActivationStatusEnum.ACTIVATED.value:
                is_activated=True
            
            ic(is_activated)
            data['activated']=is_activated
            ic(data['activated'])
            

            discounts:dict=distri_exists['distributors']['discounts']
            ic(discounts)
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
                    ic(discount)
                    ic(discount['id'])
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
            last_ord_expiry_date=None
            last_order_id=None
            ic(data['status_info'])
            if  data['status_info']['invoice_status']==InvoiceStatus.COMPLETED.value and data['status_info']['payment_status']==PaymentStatus.FULL_PAYMENT_RECEIVED.value:
                if data['purchase_type']==PurchaseTypes.EXISTING_ADD_ON.value:
                    last_order=(await orders_obj.get_by_id(order_id=data['last_order_id']))
                    # last_order=(await orders_obj.get_last_order(customer_id=data['customer_id'],product_id=data['product_id']))
                    if not last_order['order'] or len(last_order['order'])<1:
                        data['reason']="This Customer+Product doesn't have on existing order for creating a ADD-ON or Invalid Last Order Id"
                        skipped_items.append(data)
                        continue
                    delivery_date = datetime.strptime(
                        last_order['order']['delivery_info']['delivery_date'],
                        "%Y-%m-%d"
                    ).date()
                    expiry_date=delivery_date+timedelta(days=DEFAULT_ADDON_YEAR+1)
                    remaining_days=get_remaining_days(from_date=expiry_date,to_date=data['delivery_info']['delivery_date'])
                    if remaining_days>365:
                        data['last_order']=last_order
                        data['remaing_days']=remaining_days
                        data['reason']="Date mistmatch for creating ADD-ON,Date excedding >365"
                        skipped_items.append(data)
                        continue
                    ic(last_order)
                    data['unit_price']=last_order['order']['unit_price']
                    paid_amount=get_customer_addon_price(customer_price=data['unit_price'],qty=data['quantity'],expiry_date=expiry_date,delivery_date=data['delivery_info']['delivery_date']).get("with_gst")
                
                else:
                    paid_amount=get_customer_price(customer_price=data['unit_price'],qty=data['quantity']).get('with_gst')
                    ic(paid_amount)


            if data['purchase_type']==PurchaseTypes.EXISTING_ADD_ON.value:
                last_order=(await orders_obj.get_by_id(order_id=data['last_order_id']))
                # last_order=(await orders_obj.get_last_order(customer_id=data['customer_id'],product_id=data['product_id']))
                if not last_order['order'] or len(last_order['order'])<1:
                    data['reason']="This Customer+Product doesn't have on existing order for creating a ADD-ON or Invalid Last Order Id"
                    skipped_items.append(data)
                    continue
                else:  
                    delivery_date = datetime.strptime(
                        last_order['order']['delivery_info']['delivery_date'],
                        "%Y-%m-%d"
                    ).date() 
                    last_order_date=delivery_date
                    last_ord_expiry_date=last_order_date
                    last_order_id=last_order['order']['id']
                    data['unit_price']=last_order['order']['unit_price']
                    paid_amount=0

            data['status_info']['paid_amount']=round(paid_amount)

            data['logistic_info']=LogisticsInfo(
                last_ord_expiry_date=last_ord_expiry_date,
                last_order_id=last_order_id,
                purchase_type=data['purchase_type'],
                renewal_type=data['renewal_type'],
                bill_to=data['bill_to'],
                distributor_type=data['distributor_type']
            )

            last_ord_expiry_date=None
            last_order_id=None

            data['additional_discount']=f"{data['discount']*100}%"
            order_id:str=generate_uuid()
            cur_uiid=generate_ui_id(prefix=LUI_ID_ORDER_PREFIX,last_id=lui_id)
            lui_id=cur_uiid
            del data['existing_discounts']
            del data['converted_discounts']
            del data['last_order_id']

            
            # skipped_items.append(data)
            ic(data['logistic_info']['renewal_type'])
            if data['logistic_info']['renewal_type']==RenewalTypes.YEARLY_YEARLY_BILL.value or data['logistic_info']['renewal_type']==RenewalTypes.MONTHLY_BILL_MONTHLY_COMMITMENT.value:
                status_infotoadd.append(OrdersPaymentInvoiceInfo(**data['status_info'],order_id=order_id))
                data['status_info']=[data['status_info']]
                ic(data['activated'])
                ic("Hii inside")
                formatted_schema=AddOrderDbSchema(**data,id=order_id,ui_id=cur_uiid).model_dump(mode='json',exclude_unset=True,exclude_none=True,exclude=['status_info','last_order_id'])
                search_fields=AddSearchField(
                    ui_id=cur_uiid,
                    id=order_id,
                    distributor_id=data['discount_id'],
                    customer_id=data['customer_id'],
                    product_id=data['product_id'],
                    distributor_name=distri_exists['distributors']['name'],
                    distributor_ui_id=distri_exists['distributors']['ui_id'],
                    product_name=prod_exists['product']['name'],
                    product_type=prod_exists['product']['product_type'],
                    product_ui_id=prod_exists['product']['ui_id'],
                    customer_email=', '.join(cust_exists['customer']['emails']),
                    customer_name=cust_exists['customer']['name'],
                    customer_ui_id=cust_exists['customer']['ui_id'],
                )

                searchable_data.append(search_fields)
                datas_toadd.append(Orders(**formatted_schema))
            else:
                data['reason']="YEARLY_YEARLY_BILL and MONTHLY_BILL_MONTHLY_COMMITMENT only Allowed"
                skipped_items.append(data)
            
            is_activated=False
            discount_id=None

        
        skipped_file_path = write_skipped_items_to_excel(skipped_items)
        
        ic("skipped_items_count", len(skipped_items))
        ic("orders_to_insert_count", len(datas_toadd))
        ic("Skipped file path",skipped_file_path)
        if len(skipped_items)>0:
            blob_name=upload_excel_to_blob(local_file_path=skipped_file_path)
            url=generate_sas_url(blob_name=blob_name)
            ic(url)
            msg=sse_msg_builder(title="Skiped datas report",description=f"During bulk upload these are the datas are skipped, Skipped Items Count ({len(skipped_items)}), Added Items Count ({len(datas_toadd)})",type="file",url=url)
            is_sended=await sse_manager.send(self.cur_user_id,data=msg)
            if not is_sended:
                user=await UserRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).get_by_id(userid_toget=self.cur_user_id)
                user_email=user['user']['email']
                await send_email(client_ip="",reciver_emails=[user_email],subject="Skiped datas report",body=f"Skipped Items Count ({len(skipped_items)}), Added Items Count ({len(datas_toadd)}), During bulk upload these are the datas are skipped -> {url}",is_html=False,sender_email_id="crm@tibos.in")

        # await OrderSearch().create_bulk_doc(searchable_data)
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


        if data.logistic_info.get("purchase_type")==PurchaseTypes.EXISTING_ADD_ON.value:
            last_order=(await order_obj.get_by_id(order_id=data.last_order_id))
            # last_order=(await orders_obj.get_last_order(customer_id=data['customer_id'],product_id=data['product_id']))
            if not last_order['order'] or len(last_order['order'])<1:
                return ErrorResponseTypDict(status_code=400,success=False,msg="Error : Adding Order",description="Invalid Last Order")
            ic(last_order)
            data_toupdate['logistic_info']['last_order_id']=data.last_order_id
            data_toupdate['logistic_info']['last_ord_expiry_date']=last_order['order']['delivery_info']['delivery_date']

        search_fields=UpdateSearchField(
            distributor_name=distri_exists['distributors']['name'],
            distributor_ui_id=distri_exists['distributors']['ui_id'],
            product_name=prod_exists['product']['name'],
            product_type=prod_exists['product']['product_type'],
            product_ui_id=prod_exists['product']['ui_id'],
            customer_email=', '.join(cust_exists['customer']['emails']),
            customer_name=cust_exists['customer']['name'],
            customer_ui_id=cust_exists['customer']['ui_id'],
        ).model_dump(mode="json")

        # await OrderSearch().update_document(data=search_fields,id=data.order_id)

        return await OrdersRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).update(data=UpdateOrderDbSchema(**data_toupdate))


    @catch_errors    
    async def delete(self,order_id:str,customer_id:str,soft_delete:bool=True):
        # await OrderSearch().delete_document(id=order_id)
        return await OrdersRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).delete(order_id=order_id,customer_id=customer_id,soft_delete=soft_delete)
    

    @catch_errors    
    async def delete_bulk(self,data:OrderBulkDeleteSchema,soft_delete:bool=True):
        data=OrderBulkDeleteDbSchema(order_ids=data.order_ids)
        await OrderSearch().delete_bulk_doc(ids=data.order_ids)
        return await OrdersRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).delete_bulk(data=data,soft_delete=soft_delete)
    
    @catch_errors  
    async def recover(self,order_id:str,customer_id:str):
        order=await self.get_by_id(order_id=order_id,include_delete=True)
        order_info=order['order']
        search_fields=AddSearchField(
            distributor_id=order_info['distributor_id'],
            customer_id=order_info['customer_id'],
            product_id=order_info['product_id'],
            distributor_name=order_info['distributors_name'],
            distributor_ui_id=order_info['distributors_ui_id'],
            product_name=order_info['product_name'],
            product_type=order_info['product_type'],
            product_ui_id=order_info['product_ui_id'],
            customer_email=order_info['customer_email'],
            customer_name=order_info['customer_name'],
            customer_ui_id=order_info['customer_ui_id'],
        ).model_dump(mode="json")

        # await OrderSearch().create_document(data=search_fields)
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
    async def get_by_id(self,order_id:str,include_delete:bool=False):
        return await OrdersRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).get_by_id(order_id=order_id,include_delete=include_delete)
        
    @catch_errors
    async def get_by_customer_id(self,customer_id:str,cursor:int,limit:int):
        return await OrdersRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).get_by_customer_id(customer_id=customer_id,cursor=cursor,limit=limit)
    
    @catch_errors
    async def get_last_order(self,customer_id:str,product_id:str):
        return await OrdersRepo(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).get_last_order(customer_id=customer_id,product_id=product_id)



