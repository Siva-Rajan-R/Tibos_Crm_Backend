from icecream import ic
from . import HTTPException
from cryptography.fernet import Fernet
import os


class SymmetricEncryption:
    def __init__(self,secret_key:str):
        self.secret_key=secret_key
        self.symme=Fernet(key=self.secret_key)

    def encrypt_data(self,data:str)->str:
        """It will get a string data and encrypt that data using symmetric encryption"""

        try:
            encrypted_data=self.symme.encrypt(data=data.encode())
            return encrypted_data.decode()
        
        except Exception as e:
            ic(f"something went wrong while encrypting data {e}")
            raise HTTPException(
                status_code=500,
                detail=f"something went wrong while encrypting data {e}"
            )

    def decrypt_data(self,encrypted_data:str)->str:
        """It will get a encrypted string data and decrypt that data using symmetric encryption"""

        try:
            decrypted_data=self.symme.decrypt(token=encrypted_data.encode())
            return decrypted_data.decode()
        
        except Exception as e:
            ic(f"something went wrong while decrypting data {e}")
            raise HTTPException(
                status_code=500,
                detail=f"something went wrong while decrypting data {e}"
            )