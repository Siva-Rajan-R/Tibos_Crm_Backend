from database.models.fb_models.user import USER_MODEL,fdb,DEFAULT_SUPERADMIN_INFO
from pydantic import EmailStr
from security.jwt_token import generate_jwt_token,ACCESS_JWT_KEY,REFRESH_JWT_KEY,JWT_ALG
from utils.uuid_generator import generate_uuid
from data_formats.enums.common_enums import UserRoles
from globals.fastapi_globals import HTTPException
from icecream import ic



class AuthCrud:

    def __sanitize_email(self,email:EmailStr):
        return email.replace('@','_').replace('.','_')
    
    def check_email_isexists(self,email:EmailStr):
        user_data=fdb.child(USER_MODEL).child(self.__sanitize_email(email)).get().val()
        if not user_data:
            return False
        return user_data
    

    def init_superadmin(self):
        try:
            ic("🔃 Creating Default Super-Admin... ")
            self.add_update(
                email=DEFAULT_SUPERADMIN_INFO['email'],
                name=DEFAULT_SUPERADMIN_INFO['name'],
                role=UserRoles.SUPER_ADMIN
            )
            ic("✅ Default Super-Admin Created Successfully")
        except HTTPException:
            raise
        except Exception as e:
            ic(
                f"❌ Error : Creating Default Super-Admin {e}"
            )
    
    
    def add_update(self,email:EmailStr,name:str,role:UserRoles):
        try:
            user=self.check_email_isexists(email=email)
            role=user['role'] if user else role.value
            if not user:
                user_id=generate_uuid(name)
                user_data={
                    'id':user_id,
                    'email':email,
                    'name':name,
                    'role':role
                }
                
                fdb.child(USER_MODEL).child(self.__sanitize_email(email=email)).set(user_data)
                ic("User Added Successfully")
            data={'email':email,'role':role}
            access_token=generate_jwt_token(data={'data':data},secret=ACCESS_JWT_KEY,alg=JWT_ALG,exp_min=15)
            refresh_token=generate_jwt_token(data={'data':data},secret=REFRESH_JWT_KEY,alg=JWT_ALG,exp_day=7)
            
            return {
                'access_token':access_token,
                'refresh_token':refresh_token
            }
        
        except HTTPException:
            raise

        except Exception as e:
            ic(f"Something went wrong while add-update user {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Something went wrong while add-update user {e}"
            )
        
    def update_role(self,user_role:UserRoles,email_toupdate:EmailStr,role_toupdate:UserRoles):
        try:
            ic(user_role,"from update role",UserRoles.SUPER_ADMIN)
            if user_role!=UserRoles.SUPER_ADMIN.value:
                raise HTTPException(
                    status_code=401,
                    detail="Invalid user"
                )
            user_toupdate=self.check_email_isexists(email=email_toupdate)
            if not user_toupdate:
                raise HTTPException(
                    status_code=404,
                    detail="User not found"
                )
            ic(f"Before Role Update : {user_toupdate}")
            user_toupdate['role']=role_toupdate.value
            ic(f"After Role Update : {user_toupdate}")

            fdb.child(USER_MODEL).child(self.__sanitize_email(email=email_toupdate)).set(user_toupdate)

            return "User role updated successfully"
        
        except HTTPException:
            raise

        except Exception as e:
            ic(f"Something went wrong while updating user role {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Something went wrong while updating user role {e}"
            )

    
    def delete(self,user_role:UserRoles,email_toremove:EmailStr):
        try:
            if user_role!=UserRoles.SUPER_ADMIN.value:
                raise HTTPException(
                    status_code=401,
                    detail="Invalid user"
                )
            
            is_removed=fdb.child(USER_MODEL).child(self.__sanitize_email(email=email_toremove)).remove()
            ic(f"isuser removed {is_removed}")
            return "user removed successfully"
        
        except HTTPException:
            raise

        except Exception as e:
            ic(f"Something went wrong while deleting user {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Something went wrong while deleting user {e}"
            )
    
    def get(self,user_role:UserRoles):
        try:
            if user_role==UserRoles.SUPER_ADMIN.value or user_role==UserRoles.ADMIN.value:
                users=fdb.child(USER_MODEL).get().val()
                ic(f"User : {users}")
                return {'users':users}
            
            raise HTTPException(
                status_code=401,
                detail="Invalid User"
            )
        
        except HTTPException:
            raise

        except Exception as e:
            ic(f"Something went wrong while getting all user {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Something went wrong while getting all user {e}"
            )
    
    def get_by_email(self,email_toget:EmailStr,user_role:UserRoles):
        try:
            if user_role==UserRoles.SUPER_ADMIN.value or user_role==UserRoles.ADMIN.value:
                user=fdb.child(USER_MODEL).child(self.__sanitize_email(email=email_toget)).get().val()
                ic(f"User : {user}")
                return {'user':user}
            
            raise HTTPException(
                status_code=401,
                detail="Invalid User"
            )
        
        except HTTPException:
            raise

        except Exception as e:
            ic(f"Something went wrong while getting single user {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Something went wrong while getting single user {e}"
            )
    
    def get_by_role(self,role_toget:UserRoles):
        users=fdb.child(USER_MODEL).order_by_child('role').equal_to(role_toget.value).get().val()
        ic(f"{role_toget.name} : {users}")
        if users!=[]:
            return [val['email'] for key,val in users.items()]
        return []
