from fastapi import Request,HTTPException,Depends
from infras.primary_db.main import get_pg_db_session,AsyncSession
from fastapi.security import HTTPBearer,HTTPAuthorizationCredentials
from security.jwt_token import decode_jwt_token,ACCESS_JWT_KEY,REFRESH_JWT_KEY,JWT_ALG
from ..handlers.user_handler import HandleUserRequest
from infras.primary_db.repos.user_repo import UserRepo
from core.data_formats.enums.user_enums import UserRoles
from icecream import ic
from infras.caching.models.auth_model import get_auth_revoke,set_auth_revoke,unlink_auth_revoke,unlink_auth_forgot,get_auth_forgot,set_auth_forgot
from core.constants import ROLES_ALLOWED
from models.response_models.req_res_models import ErrorResponseTypDict,BaseResponseTypDict,SuccessResponseTypDict

bearer=HTTPBearer()

async def verify_user(request:Request,credentials:HTTPAuthorizationCredentials=Depends(bearer),session:AsyncSession=Depends(get_pg_db_session)):
    bearer_token=credentials.credentials
    ic(f"credentials : {bearer_token}")
    
    secret=ACCESS_JWT_KEY
    if request.url.path=='/auth/token/new':
        secret=REFRESH_JWT_KEY

    decoded_token=decode_jwt_token(
        token=bearer_token,
        secret=secret,
        alg=JWT_ALG
    )

    if not await check_permission(request=request,role=decoded_token.get('role')):
        raise HTTPException(
            status_code=403,
            detail=ErrorResponseTypDict(
                status_code=403,
                msg="Error : ",
                description="Insufficient permission",
                success=False
            ).model_dump(mode='json')
        )
    
    extracted_user_id:str=decoded_token.get('id')
    extracted_user_role:str=decoded_token.get('role')
    extracted_user_email:str=decoded_token.get('email')
    extracted_user_token_version:float=decoded_token.get('token_version')

    if await get_auth_revoke(user_id=extracted_user_id):

        user=await UserRepo(session=session,user_role=UserRoles.SUPER_ADMIN,cur_user_id="").isuser_exists(include_deleted=False,user_id_email=extracted_user_id)
        ic(user)
        if not user:
            raise HTTPException(
                status_code=401,
                detail=ErrorResponseTypDict(
                    status_code=401,
                    msg="Error : verifying Token",
                    description="User does not exists",
                    success=False
                ).model_dump(mode='json')
            )
        if user['token_version']!=extracted_user_token_version:
            raise HTTPException(
                status_code=401,
                detail=ErrorResponseTypDict(
                    status_code=401,
                    msg="Error : verifying Token",
                    description="Some of your info (Pwd,Name,Role) are changed, please login again",
                    success=False
                ).model_dump(mode='json')
            )

    return decoded_token


async def check_permission(request:Request,role:str):
    prefix=request.url.path.split('/')[1]
    method=request.method.upper()
    ic(prefix,method)

    if ROLES_ALLOWED[role]=={}:
        return True
    
    if ROLES_ALLOWED[role] is None:
        return False

    is_none=ROLES_ALLOWED[role].get(prefix,{})

    if is_none is None:
        return False
    
    if is_none=={}:
        return True
    
    ic(ROLES_ALLOWED[role][prefix]-{method})
    cur_role_len=len(ROLES_ALLOWED[role][prefix])
    temp_role_len=len(ROLES_ALLOWED[role][prefix]-{method})

    if cur_role_len!=temp_role_len:
        return True
    

    
