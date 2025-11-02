from configs.argon2_config import hasher,VerifyMismatchError,VerificationError

from icecream import ic
from globals.fastapi_globals import HTTPException



def hash_data(data:str)->str:
    """It will get a string data and hash that data using argon2-cffi"""

    try:
        return hasher.hash(password=data)
    
    except Exception as e:
        ic(f"something went wrong while hashing data {e}")
        raise HTTPException(
            status_code=500,
            detail=f"something went wrong while hashing data {e}"
        )
    

def verfiy_hashed(plain_data:str,hashed_data:str)->bool:
    """It will take a hashed data and plain data to check wheather it is true or false """

    try:
        return hasher.verify(hash=hashed_data,password=plain_data)
    
    except VerifyMismatchError:
        ic(f"invalid hash || plain data")
        raise HTTPException(
            status_code=401,
            detail=f"invalid hash || plain hash"
        )
    
    except Exception as e:
        ic(f"something went wrong while verifying hash {e}")
        raise HTTPException(
            status_code=500,
            detail=f"something went wrong while verifying hash {e}"
        )