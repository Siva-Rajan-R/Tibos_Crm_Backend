from infras.primary_db.services.user_service import UserService
from infras.primary_db.repos.user_repo import UserRepo
from sqlalchemy.ext.asyncio import AsyncSession
from icecream import ic
from core.data_formats.enums.common_enums import UserRoles
from pydantic import EmailStr
from core.decorators.error_handler_dec import catch_errors
from . import HTTPException,ErrorResponseTypDict,SuccessResponseTypDict,BaseResponseTypDict
from . import Request,Response
from security.twofactor_generator import generate_2factor_qr,generate_2factor_secret,verify_2factor
from infras.caching.models.redis_model import unlink_redis,set_redis,get_redis
from schemas.request_schemas.twofactor import TwoFactorOtpSchema
from fastapi.responses import StreamingResponse



class Handle2FactorRequest:
    """on this calss have a multiple methods"""
    def __init__(self,session:AsyncSession):
        self.session=session
        

    @catch_errors
    async def generate(self,user_id:str,request:Request):
        user=await UserRepo(session=self.session,user_role=UserRoles.SUPER_ADMIN).isuser_exists(user_id_email=user_id)
        ic(user)
        user_email:EmailStr=user['email']
        is_2factor_enabled:bool=user['tf_secret']
        if is_2factor_enabled:
            raise HTTPException(
                status_code=409,
                detail=ErrorResponseTypDict(
                    status_code=409,
                    success=False,
                    msg="Error : Geting 2Factor qrcode",
                    description="Two facto authentication already enabled"
                ).model_dump(mode='json')
            )
        
        issuer_name="Tibos-Crm"
        secret=generate_2factor_secret()
        qrcode=generate_2factor_qr(secret=secret,user_name=user_email,issuer_name=issuer_name)

        cache_data={'secret':secret}
        cache_key=f'user-{user_id}-ip-{request.client.host}'
        await set_redis(key=cache_key,value=cache_data,expire=500)

        if qrcode:
            return StreamingResponse(
                content=qrcode,
                media_type='image/png'
            )

        
    @catch_errors
    async def verify(self,user_id:str,request:Request,data:TwoFactorOtpSchema):

        cache_key=f'user-{user_id}-ip-{request.client.host}'
        cached_data:dict=await get_redis(key=cache_key)
        await unlink_redis(key=[cache_key])
        if not cached_data:
            raise HTTPException(
                status_code=401,
                detail=ErrorResponseTypDict(
                    status_code=401,
                    success=False,
                    msg="Error : Validating twofactor",
                    description="Invalid user or Time expired , please try again later"
                ).model_dump(mode='json')
            )
        
        secret=cached_data['secret']
        if not verify_2factor(otp=data.tf_otp,secret=secret):
            raise HTTPException(
                status_code=401,
                detail=ErrorResponseTypDict(
                    status_code=401,
                    msg="Error : Verifying Otp",
                    description="Invalid Twofactor otp"
                ).model_dump(mode='json')
            )

        # res=await UserService(session=self.session,user_role=UserRoles.SUPER_ADMIN).update_twofactor(user_toupdate_id=user_id,tf_secret=secret)
        # if not res:
        #     raise HTTPException(
        #         status_code=400,
        #         detail=ErrorResponseTypDict(
        #             status_code=400,
        #             success=False,
        #             msg="Error : Verifying Two factor",
        #             description="Invalid data , try may be later"
        #         )
        #     )

        return SuccessResponseTypDict(
            detail=BaseResponseTypDict(
                status_code=201,
                msg="Two factor authentication enabled successfully",
                success=True
            )
        )