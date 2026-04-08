from fastapi import Depends,APIRouter,Query,Form,UploadFile,Query,File,Request,BackgroundTasks,HTTPException
from schemas.request_schemas.order import AddCartOrderProductSchema,AddOrderSchema,AddCartOrderSchema
from infras.primary_db.main import get_pg_db_session,AsyncSession
from api.dependencies.token_verification import verify_user
from ..handlers.order_handler import HandleOrdersRequest
from typing import Optional,List
from core.data_formats.enums.dd_enums import ImportExportTypeEnum
from schemas.request_schemas.order import OrderFilterSchema
from models.response_models.req_res_models import SuccessResponseTypDict,BaseResponseTypDict
from core.utils.export_func import create_excel_export
from infras.primary_db.repos.order_repo import OrdersRepo
from core.data_formats.enums.user_enums import UserRoles
from models.import_export_models.exports.excel_headings_mapper import ORDERS_MAPPER
from schemas.request_schemas.export import ExportFields
from tasks.arq_tasks.enqueues.report import enqueue_excel_report_job
from pydantic import EmailStr
from icecream import ic
from infras.primary_db.repos.order_repo import OrdersRepo
from ..handlers.order_cart_handler import HandleOrderCartRequest



router=APIRouter(
    tags=['Order Cart Crud'],
    prefix='/order-cart'
)



@router.post('')
async def create(data:AddCartOrderSchema,user:dict=Depends(verify_user),session:AsyncSession=Depends(get_pg_db_session)):
    return await HandleOrderCartRequest(session=session,user_role=UserRoles.SUPER_ADMIN,cur_user_id=user['id']).add(data=data)


@router.get('')
async def get(cursor:int=1,limit=10,session:AsyncSession=Depends(get_pg_db_session),user:dict=Depends(verify_user)):
    return await HandleOrderCartRequest(session=session,user_role=UserRoles.SUPER_ADMIN,cur_user_id=user['id']).get(cursor=cursor,limit=limit)