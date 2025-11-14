from database.models.pg_models.user import UserRoles,Users
from sqlalchemy import select,update,delete,and_,or_
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import EmailStr
from utils.uuid_generator import generate_uuid
from security.jwt_token import generate_jwt_token,ACCESS_JWT_KEY,REFRESH_JWT_KEY,JWT_ALG
from globals.fastapi_globals import HTTPException
from icecream import ic
import os,json
from operations.response_models.user_response import UserAddResponse
from operations.abstract_models.crud_model import UserCrudModel

DEFAULT_SUPERADMIN_INFO=json.loads(os.getenv('DEFAULT_SUPERADMIN_INFO'))

class UserCrud(UserCrudModel):
    def __init__(self,session:AsyncSession):
        self.session=session

    async def isuser_exists(self,user_id_email:str):
        return (await self.session.execute(
            select(
                Users.id,
                Users.email,
                Users.name,
                Users.role
            ).where(or_(Users.email==user_id_email,Users.id==user_id_email))
        )).mappings().one_or_none()
    

    async def init_superadmin(self):
        try:
            ic("🔃 Creating Default Super-Admin... ")
            await self.add(
                email=DEFAULT_SUPERADMIN_INFO['email'],
                name=DEFAULT_SUPERADMIN_INFO['name'],
                role=UserRoles.SUPER_ADMIN
            )
            ic("✅ Default Super-Admin Created Successfully")

        except Exception as e:
            ic(
                f"❌ Error : Creating Default Super-Admin {e}"
            )

    async def add(self,name:str,email:EmailStr,role:UserRoles)->UserAddResponse:
        try:
            async with self.session.begin():
                user_id=(await self.session.execute(select(Users.id).where(Users.email==email))).scalar_one_or_none()
                if not user_id:
                    user_id=generate_uuid(name)
                    user_toadd=Users(
                        id=user_id,
                        name=name,
                        email=email,
                        role=role
                    )

                    self.session.add(user_toadd)
                
                data={'email':email,'role':role.value,'id':user_id}
                ic(data)
                access_token=generate_jwt_token(data={'data':data},secret=ACCESS_JWT_KEY,alg=JWT_ALG,exp_day=7)
                refresh_token=generate_jwt_token(data={'data':data},secret=REFRESH_JWT_KEY,alg=JWT_ALG,exp_day=7)
                ic(f"super admin tokens : {access_token} , {refresh_token}")
                return UserAddResponse(
                    access_token=access_token,
                    refresh_token=refresh_token
                )
        
        except HTTPException:
            raise

        except Exception as e:
            ic(f"Something went wrong while add-update user {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Something went wrong while add-update user {e}"
            )
        
    async def update():
        # this is just for abstract this method doesnot do anything
        pass

    async def update_role(self,user_role:UserRoles,user_toupdate_id:str,role_toupdate:UserRoles):
        try:
            async with self.session.begin():
                if not user_role==UserRoles.SUPER_ADMIN.value:
                    raise HTTPException(
                        status_code=401,
                        detail="Your'e not allowed"
                    )
                
                userrole_toupdate=update(Users).where(Users.id==user_toupdate_id).values(
                    role=role_toupdate
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
                    Users.role
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
                Users.role
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
                Users.role
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