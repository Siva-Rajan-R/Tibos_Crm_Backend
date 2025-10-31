from configs.symme_config import symme
from icecream import ic
from gloabals.fastapi_globals import HTTPException


def encrypt_data(data:str)->str:
    """It will get a string data and encrypt that data using symmetric encryption"""

    try:
        encrypted_data=symme.encrypt(data=data.encode())
        return encrypted_data.decode()
    
    except Exception as e:
        ic(f"something went wrong while encrypting data {e}")
        raise HTTPException(
            status_code=500,
            detail=f"something went wrong while encrypting data {e}"
        )

def decrypt_data(encrypted_data:str)->str:
    """It will get a encrypted string data and decrypt that data using symmetric encryption"""

    try:
        decrypted_data=symme.decrypt(token=encrypted_data.encode())
        return decrypted_data.decode()
    
    except Exception as e:
        ic(f"something went wrong while decrypting data {e}")
        raise HTTPException(
            status_code=500,
            detail=f"something went wrong while decrypting data {e}"
        )