from fastapi import APIRouter,Depends
from api.dependencies.token_verification import verify_user
from infras.primary_db.main import AsyncSession,get_pg_db_session
from core.data_formats.enums.common_enums import UserRoles,IndianStatesEnum,OwnersEnum
from core.data_formats.enums.pg_enums import ProductTypes,CustomerSectors,ShippingMethods,CustomerIndustries,PaymentStatus,InvoiceStatus,BillingType,LeadSource,LeadStatus,OpportunityStatus
from core.data_formats.enums.payment_enums import PaymentTermsEnum

router=APIRouter(
    tags=["Drop-Downs"],
    prefix='/dd'
)

@router.get('/all')
async def get_all_dd(user:dict=Depends(verify_user)):
    return{
        'user_roles':list(UserRoles._value2member_map_.values()),
        'product_types':list(ProductTypes._value2member_map_.values()),
        'customer_sectors':list(CustomerSectors._value2member_map_.values()),
        'customer_industries':list(CustomerIndustries._value2member_map_.values()),
        'shipping_methods':list(ShippingMethods._value2member_map_.values()),
        'payment_status':list(PaymentStatus._value2member_map_.values()),
        'invoice_status':list(InvoiceStatus._value2member_map_.values()),
        'opportunity_status':list(OpportunityStatus._value2member_map_.values()),
        'billing_type':list(BillingType._value2member_map_.values()),
        'lead_status':list(LeadStatus._value2member_map_.values()),
        'lead_source':list(LeadSource._value2member_map_.values()),
        'payment_terms':list(PaymentTermsEnum._value2member_map_.values()),
        'indian_states':list(IndianStatesEnum._value2member_map_.values()),
        'owners':list(OwnersEnum._value2member_map_.values())
    }


@router.get('/user-roles')
async def get_dd_user_role(user:dict=Depends(verify_user)):
    return {
        'user_roles':list(UserRoles._value2member_map_.values())
    }

@router.get('/product-types')
async def get_dd_user_role(user:dict=Depends(verify_user)):
    return {
        'product_types':list(ProductTypes._value2member_map_.values())
    }

@router.get('/customer-sectors')
async def get_dd_user_role(user:dict=Depends(verify_user)):
    return {
        'customer_sectors':list(CustomerSectors._value2member_map_.values())
    }

@router.get('/customer-industries')
async def get_dd_user_role(user:dict=Depends(verify_user)):
    return {
        'customer_industries':list(CustomerIndustries._value2member_map_.values())
    }

@router.get('/shipping-methods')
async def get_dd_user_role(user:dict=Depends(verify_user)):
    return {
        'shipping_methods':list(ShippingMethods._value2member_map_.values())
    }

@router.get('/payment-status')
async def get_dd_payment_status(user:dict=Depends(verify_user)):
    return {
        'payment_status':list(PaymentStatus._value2member_map_.values())
    }

@router.get('/invoice-status')
async def get_dd_invoice_status(user:dict=Depends(verify_user)):
    return {
        'invoice_status':list(InvoiceStatus._value2member_map_.values())
    }

@router.get('/opportunity-status')
async def get_dd_opportunity_status(user:dict=Depends(verify_user)):
    return {
        'opportunity_status':list(OpportunityStatus._value2member_map_.values())
    }

@router.get('/billing-type')
async def get_dd_billing_type(user:dict=Depends(verify_user)):
    return {
        'billing_type':list(BillingType._value2member_map_.values())
    }

@router.get('/lead-status')
async def get_dd_lead_status(user:dict=Depends(verify_user)):
    return {
        'lead_status':list(LeadStatus._value2member_map_.values())
    }

@router.get('/lead-source')
async def get_dd_lead_source(user:dict=Depends(verify_user)):
    return {
        'lead_source':list(LeadSource._value2member_map_.values())
    }