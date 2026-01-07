from core.configs.security_configs.pyjwt_config import jwt_token,DecodeError,ExpiredSignatureError
from icecream import ic
from . import HTTPException
from datetime import datetime,timedelta,timezone
from security.symm_encryption import encrypt_data,decrypt_data
import os,json
from core.settings import SETTINGS

ACCESS_JWT_KEY=SETTINGS.ACCESS_JWT_KEY
REFRESH_JWT_KEY=SETTINGS.REFRESH_JWT_KEY
JWT_ALG=SETTINGS.JWT_ALG


def generate_jwt_token(data:dict,secret:str,alg:str,exp_min:int=0,exp_day:int=0,exp_sec:int=0)->str:
    """it will get a enough data to generate a jwt token based on the secret, alg, expirations using pyjwt"""

    try:
        data['exp']=datetime.now(timezone.utc)+timedelta(days=exp_day,minutes=exp_min,seconds=exp_sec)
        data['iss']="DeB-Auth"
        encrypted_data=encrypt_data(data=json.dumps(data['data']))
        data['data']=encrypted_data
        token=jwt_token.encode(
            payload=data,
            key=secret,
            algorithm=alg
        )
        return token

    except Exception as e:
        ic(f"something went wrong while generating jwt token {e}")
        raise HTTPException(
            status_code=500,
            detail=f"something went wrong while generating jwt token {e}"
        )
    

def decode_jwt_token(token:str,secret:str,alg:str)->dict:
    """it will get a jwt token, secret, alg to validate the data"""

    try:
        decoded_token=jwt_token.decode(
            jwt=token,
            key=secret,
            algorithms=alg
        )

        decrypted_data=json.loads(decrypt_data(encrypted_data=decoded_token['data'])) #{email:...,role:...}

        return decrypted_data
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=401,
            detail=f"Token has expired"
        )
    
    except DecodeError:
        raise HTTPException(
            status_code=401,
            detail=f"Invalid Token"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"something went wrong while decoding jwt token {e}"
        )

