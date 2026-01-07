from . import HTTPException
from models.repo_models.auth_model import AuthenticationRepo
from icecream import ic
import httpx,os,json
from core.configs.security_configs.pyjwt_config import jwt_token
from core.settings import SETTINGS

DEB_AUTH_APIKEY=SETTINGS.DEB_AUTH_APIKEY
DEB_AUTH_CLIENT_SECRET=SETTINGS.DEB_AUTH_CLIENT_SECRET

class AuthRepo(AuthenticationRepo):
    async def get_login_link(self):
        async with httpx.AsyncClient(timeout=90) as client:
            response=await client.post(
                url="https://deb-auth-api.onrender.com/auth",
                json={'apikey':DEB_AUTH_APIKEY}
            )
            if response.status_code==200:
                return response.json()
        raise HTTPException(
            status_code=response.status_code,
            detail=response.text
        )
    
    async def get_authenticated_user(self,code:str):
        async with httpx.AsyncClient(timeout=90) as client:
            response=await client.post(
                url="https://deb-auth-api.onrender.com/auth/authenticated-user",
                json={'code':code,'client_secret':DEB_AUTH_CLIENT_SECRET}
            )

            if response.status_code!=200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=response.text
                )
            
            decoded_token:dict=jwt_token.decode(response.json()['token'],options={'verify_signature':False})
            ic(decoded_token)
            return decoded_token

    
