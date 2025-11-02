from fastapi import Request,HTTPException,Depends
from fastapi.security import HTTPBearer,HTTPAuthorizationCredentials
from security.jwt_token import decode_jwt_token,ACCESS_JWT_KEY,REFRESH_JWT_KEY,JWT_ALG
from crud.auth_crud import AuthCrud,ic

bearer=HTTPBearer()
def verify_user(request:Request,credentials:HTTPAuthorizationCredentials=Depends(bearer)):
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
    user_data=AuthCrud().check_email_isexists(email=decoded_token['email'])
    if not user_data:
        raise HTTPException(
            status_code=401,
            detail="user not found"
        )
    ic(decoded_token['role'],user_data['role'])
    if decoded_token['role']!=user_data['role']:
        raise HTTPException(
            status_code=401,
            detail="Invalid User"
        )

    return decoded_token

    
