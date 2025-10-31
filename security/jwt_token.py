from configs.pyjwt_config import jwt_token
from icecream import ic
from globals.fastapi_globals import HTTPException
from datetime import datetime,timedelta,timezone
import os
from dotenv import load_dotenv
load_dotenv()

ACCESS_JWT_KEY=os.getenv("ACCESS_JWT_KEY")
REFRESH_JWT_KEY=os.getenv("REFRESH_JWT_KEY")
JWT_ALG=os.getenv("JWT_ALG")


def generate_jwt_token(data:dict,secret:str,alg:str,exp_min:int=0,exp_day:int=0,exp_sec:int=0)->str:
    """it will get a enough data to generate a jwt token based on the secret, alg, expirations using pyjwt"""

    try:
        data['exp']=datetime.now(timezone.utc)+timedelta(days=exp_day,minutes=exp_min,seconds=exp_sec)
        data['iss']="DeB-Auth"
        return jwt_token.encode(
            payload=data,
            key=secret,
            algorithm=alg
        )

    except Exception as e:
        ic(f"something went wrong while generating jwt token")
        raise HTTPException(
            status_code=500,
            detail=f"something went wrong while generating jwt token"
        )
    

def decode_jwt_token(token:str,secret:str,alg:str)->dict:
    """it will get a jwt token, secret, alg to validate the data"""

    try:
        return jwt_token.decode(
            jwt=token,
            key=secret,
            algorithms=alg
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"something went wrong while decoding jwt token {e}"
        )

