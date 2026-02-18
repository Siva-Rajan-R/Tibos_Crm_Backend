from fastapi import APIRouter,Depends
from api.dependencies.token_verification import verify_user
from infras.primary_db.main import AsyncSession,get_pg_db_session
from core.data_formats.enums.user_enums import UserRoles
from core.data_formats.enums.dd_enums import IndianStatesEnum,OwnersEnum,SettingsEnum
from core.data_formats.enums.order_enums import ShippingMethods,PaymentStatus,InvoiceStatus,BillingType,PurchaseTypes,RenewalTypes,DistributorType,PaymentTermsEnum
from core.data_formats.enums.customer_enums import CustomerSectors,CustomerIndustries
from core.data_formats.enums.product_enums import  ProductTypes
from core.data_formats.enums.lead_oppr_enums import LeadSource,LeadStatus,OpportunityStatus
from infras.primary_db.repos.dropdown_repo import DropDownRepo
from schemas.request_schemas.dropdown import AddDropDownSchema,UpdateDropDownSchema

router=APIRouter(
    tags=["Drop-Downs"],
    prefix='/dd'
)

@router.get('/all')
async def get_all_dd(user:dict=Depends(verify_user),session:AsyncSession=Depends(get_pg_db_session)):
    dd_obj=DropDownRepo(session=session)
    return [
        {'name':'settings','values':list(SettingsEnum._value2member_map_.values())},
        {'name':'user_roles','values':list(UserRoles._value2member_map_.values())},
        {'name':'indian_states','values':list(IndianStatesEnum._value2member_map_.values())},
        *(await dd_obj.get())
    ]


@router.post('')
async def add(data:AddDropDownSchema,user:dict=Depends(verify_user),session:AsyncSession=Depends(get_pg_db_session)):
    return await DropDownRepo(session=session).add(data=data)

@router.put('')
async def update(data:UpdateDropDownSchema,user:dict=Depends(verify_user),session:AsyncSession=Depends(get_pg_db_session)):
    return await DropDownRepo(session=session).update(data=data)

@router.delete('/{name}/{index}')
async def delete(name:str,index:int,user:dict=Depends(verify_user),session:AsyncSession=Depends(get_pg_db_session)):
    return await DropDownRepo(session=session).delete(name=name,index=index)

@router.get('')
async def get_all(user:dict=Depends(verify_user),session:AsyncSession=Depends(get_pg_db_session)):
    return await DropDownRepo(session=session).get()

@router.get('/by/name/{name}')
async def get_all(name:str,user:dict=Depends(verify_user),session:AsyncSession=Depends(get_pg_db_session)):
    return await DropDownRepo(session=session).getby_name(name=name)

