from fastapi import Request,HTTPException
from security.jwt_token import decode_jwt_token,ACCESS_JWT_KEY,REFRESH_JWT_KEY,JWT_ALG


def verify_user(request:Request):
    bearer_token=request.headers.get("Authorization")
    if not bearer_token:
        raise HTTPException(
            status_code=401,
            detail="Token not found"
        )
    
    bearer,token=bearer_token.split(' ')

    if (not bearer or not token) or (bearer.strip()=="" or token.strip()==""):
        raise HTTPException(
            status_code=401,
            detail="Invalid token"
        )
    
    secret=ACCESS_JWT_KEY
    if request.url.path=='/token/new':
        secret=REFRESH_JWT_KEY

    decoded_token=decode_jwt_token(
        token=token,
        secret=secret,
        alg=JWT_ALG
    )

    fb_db=""
    if decoded_token['id'] != fb_db:
        raise HTTPException(
            status_code=401,
            detail="user not found"
        )
    
    return decoded_token

    
