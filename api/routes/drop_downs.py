from fastapi import APIRouter,Depends
from api.dependencies.token_verification import verify_user
from database.configs.pg_config import AsyncSession,get_pg_db_session
from data_formats.enums.common_enums import UserRoles
from data_formats.enums.pg_enums import ProductTypes,CustomerSectors,ShippingMethods,CustomerIndustries,PaymentStatus,InvoiceStatus

router=APIRouter(
    tags=["Drop-Downs"]
)

@router.get('/dd/user-roles')
async def get_dd_user_role(user:dict=Depends(verify_user)):
    return {
        'user_roles':list(UserRoles._value2member_map_.values())
    }

@router.get('/dd/product-types')
async def get_dd_user_role(user:dict=Depends(verify_user)):
    return {
        'product_types':list(ProductTypes._value2member_map_.values())
    }

@router.get('/dd/customer-sectors')
async def get_dd_user_role(user:dict=Depends(verify_user)):
    return {
        'customer_sectors':list(CustomerSectors._value2member_map_.values())
    }

@router.get('/dd/customer-industries')
async def get_dd_user_role(user:dict=Depends(verify_user)):
    return {
        'customer_industries':list(CustomerIndustries._value2member_map_.values())
    }

@router.get('/dd/shipping-methods')
async def get_dd_user_role(user:dict=Depends(verify_user)):
    return {
        'shipping_methods':list(ShippingMethods._value2member_map_.values())
    }

@router.get('/dd/payment-status')
async def get_dd_payment_status(user:dict=Depends(verify_user)):
    return {
        'payment_status':list(PaymentStatus._value2member_map_.values())
    }

@router.get('/dd/invoice-status')
async def get_dd_invoice_status(user:dict=Depends(verify_user)):
    return {
        'invoice_status':list(InvoiceStatus._value2member_map_.values())
    }