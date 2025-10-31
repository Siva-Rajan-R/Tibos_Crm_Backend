from database.models.fb_models.user import USER_MODEL,fdb
from pydantic import EmailStr
from security.jwt_token import generate_jwt_token,ACCESS_JWT_KEY,REFRESH_JWT_KEY,JWT_ALG
from utils.uuid_generator import generate_uuid
from data_formats.enums.common_enums import UserRoles
from globals.fastapi_globals import HTTPException
from icecream import ic



class AuthCrud:

    def __sanitize_email(self,email:EmailStr):
        return email.replace('@','_').replace('.','_')
    
    def __combine_email_and_id(self,id:str,email:EmailStr):
        sanitized_mail=self.__sanitize_email(email)
        return f"{id},{sanitized_mail}"
    
    def check_email_isexists(self,email:EmailStr):
        user_data=fdb.child(USER_MODEL).child(self.__sanitize_email(email)).get().val()
        ic(user_data)
        if not user_data:
            return False
        return user_data
    
    def add_update(self,email:EmailStr,name:str,role:UserRoles):
        if not self.check_email_isexists(email=email):
            user_id=generate_uuid(name)
            user_data={
                'id':user_id,
                'email':email,
                'name':name,
                'role':role.value
            }
            
            fdb.child(USER_MODEL).child(self.__sanitize_email(email=email)).set(user_data)
            ic("User Added Successfully")
        
        access_token=generate_jwt_token(data={'id':email},secret=ACCESS_JWT_KEY,alg=JWT_ALG,exp_min=15)
        refresh_token=generate_jwt_token(data={'id':email},secret=REFRESH_JWT_KEY,alg=JWT_ALG,exp_day=7)
        
        return {
            'access_token':access_token,
            'refresh_token':refresh_token
        }
    
    def delete(self,user_email:EmailStr,email_toremove:EmailStr):
        if user_email!="siva967763@gmail.com":
            raise HTTPException(
                status_code=401,
                detail="Invalid user"
            )
        is_removed=fdb.child(USER_MODEL).child(self.__sanitize_email(email=email_toremove)).remove()
        ic(f"isuser removed {is_removed}")
        return "user removed successfully"
    
    def get(self):
        users=fdb.child(USER_MODEL).get().val()
        ic(f"User : {users}")
        return {'users':users}
    
    def get_by_email(self,user_email:EmailStr):
        user=fdb.child(USER_MODEL).child(self.__sanitize_email(user_email)).get().val()
        ic(f"User : {user}")
        return {'user':user}
        


if __name__=="__main__":
    obj=AuthCrud()
    print(obj.add_update(email="jeeva@gmail.com",name="Jeeva",role=UserRoles.USER))