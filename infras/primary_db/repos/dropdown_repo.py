from ..models.dropdown import DropDownValues
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from core.decorators.db_session_handler_dec import start_db_transaction
from sqlalchemy import select,update,delete
from schemas.request_schemas.dropdown import AddDropDownSchema,UpdateDropDownSchema
from core.data_formats.enums.user_enums import UserRoles
from core.data_formats.enums.dd_enums import IndianStatesEnum,OwnersEnum,SettingsEnum
from core.data_formats.enums.order_enums import ShippingMethods,PaymentStatus,InvoiceStatus,BillingType,PurchaseTypes,RenewalTypes,DistributorType,PaymentTermsEnum
from core.data_formats.enums.customer_enums import CustomerSectors,CustomerIndustries
from core.data_formats.enums.product_enums import  ProductTypes
from core.data_formats.enums.lead_oppr_enums import LeadSource,LeadStatus,OpportunityStatus




class DropDownRepo:
    def __init__(self,session:AsyncSession):
        self.session=session

    @start_db_transaction
    async def init_dd(self):
        datas_toadd={
            'product_types':list(ProductTypes._value2member_map_.values().mapping),
            'customer_sectors':list(CustomerSectors._value2member_map_.values().mapping),
            'customer_industries':list(CustomerIndustries._value2member_map_.values().mapping),
            'shipping_methods':list(ShippingMethods._value2member_map_.values().mapping),
            'payment_status':list(PaymentStatus._value2member_map_.values().mapping),
            'invoice_status':list(InvoiceStatus._value2member_map_.values().mapping),
            'opportunity_status':list(OpportunityStatus._value2member_map_.values().mapping),
            'billing_type':list(BillingType._value2member_map_.values().mapping),
            'lead_status':list(LeadStatus._value2member_map_.values().mapping),
            'lead_source':list(LeadSource._value2member_map_.values().mapping),
            'payment_terms':list(PaymentTermsEnum._value2member_map_.values().mapping),
            'owners':list(OwnersEnum._value2member_map_.values().mapping),
            'renewal_types':list(RenewalTypes._value2member_map_.values().mapping),
            'purchase_types':list(PurchaseTypes._value2member_map_.values().mapping),
            'distributor_types':list(DistributorType._value2member_map_.values().mapping),
        }

        formated_data=[]
        for name,values in datas_toadd.items():
            formated_data.append(DropDownValues(name=name,values=values))

        self.session.add_all(formated_data)
        return True
        

    @start_db_transaction
    async def add(self,data:AddDropDownSchema):
        self.session.add(**data.model_dump(mode='json'))
        return True
    
    @start_db_transaction
    async def update(self,data:UpdateDropDownSchema):
        dd_toupdate=update(
            DropDownValues
        ).where(
            DropDownValues.name==data.name
        ).values(
            values=data.values
        ).returning(DropDownValues.id)

        is_updated=(await self.session.execute(dd_toupdate)).scalar_one_or_none()

        return is_updated
    
    async def get(self):
        dd_stmt=select(
            DropDownValues.name,
            DropDownValues.values
        )

        dd_results=(await self.session.execute(dd_stmt)).mappings().all()

        return dd_results
    
    async def getby_name(self,name:str):
        dd_stmt=select(
            DropDownValues.name,
            DropDownValues.values
        ).where(
            DropDownValues.name==name
        )

        dd_results=(await self.session.execute(dd_stmt)).mappings().all()

        return dd_results
    
    @start_db_transaction
    async def delete(self,name:str,index:int):
        previous_values:list=(await self.getby_name(name=name))['values']
        previous_values.pop(index)
        dd_todel=update(
            DropDownValues
        ).where(
            DropDownValues.name==name
        ).values(
            values=previous_values
        ).returning(DropDownValues.id)

        is_deleted=(await self.session.execute(dd_todel)).scalar_one_or_none()

        return is_deleted