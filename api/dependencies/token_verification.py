from fastapi import Request,HTTPException,Depends
from infras.primary_db.main import get_pg_db_session,AsyncSession
from fastapi.security import HTTPBearer,HTTPAuthorizationCredentials
from security.jwt_token import decode_jwt_token,ACCESS_JWT_KEY,REFRESH_JWT_KEY,JWT_ALG
from ..handlers.user_handler import HandleUserRequest
from infras.primary_db.repos.user_repo import UserRepo
from core.data_formats.enums.common_enums import UserRoles
from icecream import ic
from infras.caching.models.redis_model import get_redis,set_redis,unlink_redis
from core.constants import ROLES_ALLOWED
from models.response_models.req_res_models import ErrorResponseTypDict,BaseResponseTypDict,SuccessResponseTypDict

bearer=HTTPBearer()

async def verify_user(request:Request,credentials:HTTPAuthorizationCredentials=Depends(bearer),session:AsyncSession=Depends(get_pg_db_session)):
    ip=request.client.host
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

    ic(request.url.path)
    ic(secret,decoded_token)
    user_id:str=decoded_token.get('id')
    ic(user_id)

    is_ipexists=False
    # checking if the incoming ip has already validated or not
    if res:=(await get_redis(f"token-verify-{user_id}")):
        ic('redis response',res)
        if res['ip']==ip:
        # if this both conditions met it will return the decoded token
            if res['count']>=3 and res['id']==user_id:
                # *important need to revoke if the role was change after 3 attempts
                ic('verified and returned via redis')
                return decoded_token
            else:
                """
                if the count is lesser and token is same means then only it will increase,
                otherwise it will unlink and create a new one after the pg db verification
                """
                if res['count']<3 and res['id']==user_id:
                    is_ipexists=True
                    res['count']=res['count']+1
                    await set_redis(f"token-verify-{user_id}",res,expire=300)
                else:
                    await unlink_redis(key=[f"token-verify-{user_id}"])

    user_data=(await UserRepo(session=session,user_role='',cur_user_id='').isuser_exists(user_id_email=decoded_token['email']))
    ic(user_data)
    if not user_data:
        raise HTTPException(
            status_code=401,
            detail=ErrorResponseTypDict(
                status_code=401,
                msg="Error : ",
                description="Invalid User",
                success=False
            ).model_dump(mode='json')
        )
    
    ic(decoded_token['role'],user_data['role'])

    if decoded_token['role']!=user_data['role']:
        raise HTTPException(
            status_code=401,
            detail=ErrorResponseTypDict(
                msg="Error : ",
                description="User role changed, please login again",
                status_code=401,
                success=False
            ).model_dump(mode='json')
        )

    if not is_ipexists:
        ic('setting token,count for the ip')
        await set_redis(f"token-verify-{user_id}",{'id':user_id,'count':0,'ip':ip})

    ic('verified and returned via pg')
    ic("decoded token : ",decoded_token['email'])
    await session.close()
    return decoded_token


async def check_permission(request:Request,role:str):
    prefix=request.url.path.split('/')[1]
    method=request.method.upper()
    ic(prefix,method)
    # If the roles_allowed is empty set means all the methods and routes are allowed for that role
    # if the roles_allowed is None means none of  methods and routes are allowed
    # if the roles_allowed is does not exists for the given route prefix means all the routes and methods are not allowed
    # if the roles_allowed is exists and the prefix is exists means we need to findout the incoming method is aloowed are not

    if ROLES_ALLOWED[role]=={}:
        return True
    
    if ROLES_ALLOWED[role] is None:
        return False

    is_none=ROLES_ALLOWED[role].get(prefix,{})

    if is_none is None:
        return False
    
    if is_none=={}:
        return True
    
    if ROLES_ALLOWED[role][prefix]-{method}:
        return False
    

    
