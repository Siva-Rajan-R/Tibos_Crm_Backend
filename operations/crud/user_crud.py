from database.models.pg_models.user import UserRoles,Users
from sqlalchemy import select,update,delete,and_,or_,func
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import EmailStr
from utils.uuid_generator import generate_uuid
from security.jwt_token import generate_jwt_token,ACCESS_JWT_KEY,REFRESH_JWT_KEY,JWT_ALG
from globals.fastapi_globals import HTTPException
from icecream import ic
import os,json
from operations.response_models.user_response import UserAddResponse
from operations.abstract_models.crud_model import UserCrudModel
from typing import Optional
from security.data_hashing import verfiy_hashed,hash_data
from secrets import token_urlsafe

DEFAULT_SUPERADMIN_INFO=json.loads(os.getenv('DEFAULT_SUPERADMIN_INFO'))
 
 
class UserCrud(UserCrudModel):
    def __init__(self,session:AsyncSession):
        self.session=session

    async def isuser_exists(self,user_id_email:str):
        return (await self.session.execute(
            select(
                Users.id,
                Users.email,
                Users.password,
                Users.name,
                Users.role,

            ).where(or_(Users.email==user_id_email,Users.id==user_id_email))
        )).mappings().one_or_none()
    

    async def init_superadmin(self):
        try:
            ic(f"🔃 Creating Default Super-Admin... {DEFAULT_SUPERADMIN_INFO} {type(DEFAULT_SUPERADMIN_INFO)}")
            for superadmins in DEFAULT_SUPERADMIN_INFO:
                await self.add(
                    user_role_tocheck=UserRoles.SUPER_ADMIN.value,
                    email=superadmins['email'],
                    name=superadmins['name'],
                    role=UserRoles.SUPER_ADMIN,
                    password=superadmins['password']
                )
            ic("✅ Default Super-Admin Created Successfully")

        except Exception as e:
            ic(
                f"❌ Error : Creating Default Super-Admin {e}"
            )

    async def add(self,user_role_tocheck:UserRoles,name:str,email:EmailStr,password:str,role:UserRoles):
        try:
            async with self.session.begin():
                if not user_role_tocheck==UserRoles.SUPER_ADMIN.value:
                    raise HTTPException(
                        status_code=401,
                        detail="Your'e not allowed"
                    )
                
                user_id=(await self.session.execute(select(Users.id).where(Users.email==email))).scalar_one_or_none()
                if user_id:
                    raise HTTPException(
                        status_code=409,
                        detail="User already exists"
                    )
                
                user_id=generate_uuid(name)
                hashed_pwd=hash_data(password)
                user_toadd=Users(
                    id=user_id,
                    name=name,
                    email=email,
                    role=role.value,
                    password=hashed_pwd
                )

                self.session.add(user_toadd)
                
                data={'email':email,'role':role.value,'id':user_id}
                ic(data)
                access_token=generate_jwt_token(data={'data':data},secret=ACCESS_JWT_KEY,alg=JWT_ALG,exp_day=7)
                refresh_token=generate_jwt_token(data={'data':data},secret=REFRESH_JWT_KEY,alg=JWT_ALG,exp_day=7)
                ic(f"super admin tokens : {access_token} , {refresh_token}")
                return "User Created Successfully"
        
        except HTTPException:
            raise

        except Exception as e:
            ic(f"Something went wrong while add-update user {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Something went wrong while add-update user {e}"
            )
    
    async def update(self,user_role:UserRoles,user_toupdate_id:str,user_toupdate_name:str,user_toupdate_role:UserRoles):
        """This is for full update *Name,Role can be changable"""
        try:
            async with self.session.begin():
                if not user_role==UserRoles.SUPER_ADMIN.value:
                    raise HTTPException(
                        status_code=401,
                        detail="Your'e not allowed"
                    )
                
                username_toupdate=update(
                    Users
                ).where(
                    Users.id==user_toupdate_id
                ).values(
                    name=user_toupdate_name,
                    role=user_toupdate_role.value
                ).returning(Users.id)
                user_id = (await self.session.execute(username_toupdate)).scalar_one_or_none()
                if not user_id:
                    raise HTTPException(
                        status_code=404,
                        detail="User not found"
                    )

                

                return 'User name and role updated Successfully'
        
        except HTTPException:
            raise

        except Exception as e:
            ic(f"Something went wrong while update user {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Something went wrong while update user {e}"
            )
        

    async def update_role(self,user_role:UserRoles,user_toupdate_id:str,role_toupdate:UserRoles):
        try:
            async with self.session.begin():
                if not user_role==UserRoles.SUPER_ADMIN.value:
                    raise HTTPException(
                        status_code=401,
                        detail="Your'e not allowed"
                    )
                
                userrole_toupdate=update(Users).where(Users.id==user_toupdate_id).values(
                    role=role_toupdate.value
                ).returning(Users.id)

                user_id=(await self.session.execute(userrole_toupdate)).scalar_one_or_none()

                if not user_id:
                    raise HTTPException(
                        status_code=404,
                        detail="Invalid user"
                    )
                
                return "User role updated successfully"
        
        except HTTPException:
            raise

        except Exception as e:
            ic(f"Something went wrong while updating user role {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Something went wrong while updating user role {e}"
            )
    
    async def update_password(self,user_toupdate_id:str,new_password:str):
        try:
            async with self.session.begin():
                
                userpwd_toupdate=update(Users).where(Users.id==user_toupdate_id).values(
                    password=hash_data(new_password)
                ).returning(Users.id)

                user_id=(await self.session.execute(userpwd_toupdate)).scalar_one_or_none()

                if not user_id:
                    raise HTTPException(
                        status_code=404,
                        detail="Invalid user"
                    )
                
                return "User password updated successfully"
        
        except HTTPException:
            raise

        except Exception as e:
            ic(f"Something went wrong while updating user password {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Something went wrong while updating user password {e}"
            )

    async def delete(self,user_role:UserRoles,userid_toremove:str):
        try:
            async with self.session.begin():
                if not user_role==UserRoles.SUPER_ADMIN.value:
                    raise HTTPException(
                        status_code=401,
                        detail="Your'e not allowed"
                    )
                
                user_todelete=delete(Users).where(userid_toremove==Users.id).returning(Users.id)
                user_id=(await self.session.execute(user_todelete)).scalar_one_or_none()
                if not user_id:
                    raise HTTPException(
                        status_code=404,
                        detail="User not found"
                    )
                
                return "User Deleted Successfully"
        
        except HTTPException:
            raise

        except Exception as e:
            ic(f"Something went wrong while deleting user {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Something went wrong while add-delete user {e}"
            )
    

    async def get(self,user_role:UserRoles):
        try:
            if not user_role==UserRoles.SUPER_ADMIN.value:
                raise HTTPException(
                    status_code=401,
                    detail="Your'e not allowed"
                )
            
            users=(await self.session.execute(
                select(
                    Users.id,
                    Users.email,
                    Users.name,
                    Users.role,
                    func.date(func.timezone("Asia/Kolkata",Users.created_at)).label("user_created_at")
                )
            )).mappings().all()

            return {'users':users}
        
        except HTTPException:
            raise

        except Exception as e:
            ic(f"Something went wrong while getting user {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Something went wrong while getting user {e}"
            )
    

    async def get_by_id(self,user_role:UserRoles,userid_toget:str):
        try:
            if not user_role==UserRoles.SUPER_ADMIN.value:
                raise HTTPException(
                    status_code=401,
                    detail="Your'e not allowed"
                )
            
            user_toget=select(
                Users.id,
                Users.name,
                Users.email,
                Users.role,
                func.date(func.timezone("Asia/Kolkata",Users.created_at)).label("user_created_at")
            ).where(
                userid_toget==Users.id
            )

            user=(await self.session.execute(user_toget)).mappings().one_or_none()

            return {'user':user}
    
        except HTTPException:
            raise

        except Exception as e:
            ic(f"Something went wrong while get-user-byid {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Something went wrong while get-user-byid {e}"
            )
    
    async def get_by_role(self,user_role:UserRoles,userrole_toget:UserRoles):
        try:
            
            if user_role!=UserRoles.SUPER_ADMIN.value:
                raise HTTPException(
                    status_code=401,
                    detail="Your'e not allowed"
                )
            
            user_toget=select(
                Users.id,
                Users.name,
                Users.email,
                Users.role,
                func.date(func.timezone("Asia/Kolkata",Users.created_at)).label("user_created_at")
            ).where(
                userrole_toget==Users.role
            )

            user=(await self.session.execute(user_toget)).mappings().all()

            return {'user':user}
    
        except HTTPException:
            raise

        except Exception as e:
            ic(f"Something went wrong while get-user-by-role {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Something went wrong while get-user-by-role {e}"
            )
    

    

    async def search():
        """this is just for abstract this method doesnot do anything"""
        pass