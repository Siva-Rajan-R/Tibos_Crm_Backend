from fastapi import APIRouter,Request,Response,Depends
from ..handlers.twofactor_handler import Handle2FactorRequest
from infras.primary_db.main import get_pg_db_session,AsyncSession
from typing import Annotated
from api.dependencies.token_verification import verify_user
from schemas.request_schemas.twofactor import TwoFactorOtpSchema


PD_SESSION=Annotated[AsyncSession,Depends(get_pg_db_session)]


router=APIRouter(
    prefix='/2factor',
    tags=['Two Factor Authentications']
)

@router.get('/qr')
async def generate_2factor_qr(request:Request,session:PD_SESSION,user: dict = Depends(verify_user)):
    user_id:str=user['id']
    return await Handle2FactorRequest(session=session).generate(user_id=user_id,request=request)


@router.post('/verify')
async def verify_2factor(data:TwoFactorOtpSchema,request:Request,session:PD_SESSION,user:dict=Depends(verify_user)):
    user_id:str=user['id']
    return await Handle2FactorRequest(session=session).verify(user_id=user_id,request=request,data=data)