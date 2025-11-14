from fastapi import Request,HTTPException,Depends
from database.configs.pg_config import get_pg_db_session
from fastapi.security import HTTPBearer,HTTPAuthorizationCredentials
from security.jwt_token import decode_jwt_token,ACCESS_JWT_KEY,REFRESH_JWT_KEY,JWT_ALG
from operations.crud.user_crud import UserCrud,ic
from database.configs.redis_config import get_redis,set_redis,unlink_redis

bearer=HTTPBearer()
async def verify_user(request:Request,credentials:HTTPAuthorizationCredentials=Depends(bearer),session=Depends(get_pg_db_session)):
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

    ic(request.url.path)
    ic(secret,decoded_token)

    is_ipexists=False
    # checking if the incoming ip has already validated or not
    if res:=(await get_redis(ip)):
        ic('redis response',res)
        # if this both conditions met it will return the decoded token
        if res['count']>=3 and res['token']==bearer_token:
            ic('verified and returned via redis')
            return decoded_token
        else:
            """
            if the count is lesser and token is same means then only it will increase,
            otherwise it will unlink and create a new one after the pg db verification
            """
            if res['count']<3 and res['token']==bearer_token:
                is_ipexists=True
                res['count']=res['count']+1
                await set_redis(ip,res,expire=300)
            else:
                await unlink_redis(key=[ip])

    user_data=(await UserCrud(session=session).isuser_exists(user_id_email=decoded_token['email']))
    ic(user_data)
    if not user_data:
        raise HTTPException(
            status_code=401,
            detail="user not found"
        )
    
    ic(decoded_token['role'],user_data['role'].value)

    if decoded_token['role']!=user_data['role'].value:
        raise HTTPException(
            status_code=401,
            detail="Invalid User"
        )

    if not is_ipexists:
        ic('setting token,count for the ip')
        await set_redis(ip,{'token':bearer_token,'count':0})

    ic('verified and returned via pg')
    ic("decoded token : ",decoded_token['email'])
    await session.close()
    return decoded_token

    
