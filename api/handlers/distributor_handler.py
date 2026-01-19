from infras.primary_db.services.distri_service import DistributorService
from core.utils.uuid_generator import generate_uuid
from sqlalchemy import select,delete,update,or_,func,String
from sqlalchemy.ext.asyncio import AsyncSession
from icecream import ic
from core.data_formats.enums.common_enums import UserRoles
from pydantic import EmailStr
from typing import Optional,List
from schemas.db_schemas.customer import AddCustomerDbSchema,UpdateCustomerDbSchema
from schemas.request_schemas.distributor import CreateDistriSchema,UpdateDistriSchema
from core.decorators.error_handler_dec import catch_errors
from math import ceil
from . import HTTPException,ErrorResponseTypDict,SuccessResponseTypDict,BaseResponseTypDict
from core.utils.discount_validator import validate_discount



class HandleDistributorRequest:
    def __init__(self,session:AsyncSession,user_role:UserRoles):
        self.session=session
        self.user_role=user_role

        if isinstance(self.user_role,UserRoles):
            self.user_role=self.user_role.value

        if self.user_role==UserRoles.USER.value:
            raise HTTPException(
                status_code=401,
                detail=ErrorResponseTypDict(
                    msg="Error : ",
                    description="Insufficient permission",
                    status_code=401,
                    success=False
                )
            )
       
    @catch_errors
    async def add(self,data:CreateDistriSchema):
        if validate_discount(data.discount) is None:
            raise HTTPException(
                status_code=400,
                detail=ErrorResponseTypDict(
                    status_code=400,
                    description="Invalid Data format for discount",
                    msg="Error : Adding Distributor",
                    success=False
                )
            )

        res = await DistributorService(session=self.session,user_role=self.user_role).add(data=data)
        if not res:
            raise HTTPException(
                status_code=400,
                detail=ErrorResponseTypDict(
                    status_code=400,
                    msg="Error : Creating Distributor",
                    description="A Distributor or Account already exists or Invalid inputs !"
                )
            )
        return SuccessResponseTypDict(
            detail=BaseResponseTypDict(
                status_code=200,
                success=True,
                msg="Distributor created successfully"
            )
        )


        
    @catch_errors  
    async def update(self,data:UpdateDistriSchema):
        if validate_discount(data.discount) is None:
            raise HTTPException(
                status_code=400,
                detail=ErrorResponseTypDict(
                    status_code=400,
                    description="Invalid Data format for discount",
                    msg="Error : Adding Distributor",
                    success=False
                )
            )
        
        res=await DistributorService(session=self.session,user_role=self.user_role).update(data=data)
        if not res:
            raise HTTPException(
                status_code=400,
                detail=ErrorResponseTypDict(
                    status_code=400,
                    success=False,
                    msg="Error : Updaing distributor",
                    description="Invalid user input"
                )
            )
        
        return SuccessResponseTypDict(
            detail=BaseResponseTypDict(
                status_code=200,
                success=True,
                msg="Distributor updated successfully"
            )
        )
        
    @catch_errors
    async def delete(self,distributor_id:str,soft_delete:bool=True):
        res=await DistributorService(session=self.session,user_role=self.user_role).delete(distributor_id=distributor_id,soft_delete=soft_delete)
        if not res:
            raise HTTPException(
                status_code=400,
                detail=ErrorResponseTypDict(
                    status_code=400,
                    success=False,
                    msg="Error : Deleting distributor",
                    description="Invalid user input"
                )
            )
        
        return SuccessResponseTypDict(
            detail=BaseResponseTypDict(
                status_code=200,
                success=True,
                msg="Distributor deleted successfully"
            )
        )

    @catch_errors
    async def recover(self,distributor_id:str):
        res=await DistributorService(session=self.session,user_role=self.user_role).recover(distributor_id=distributor_id)
        if not res:
            raise HTTPException(
                status_code=400,
                detail=ErrorResponseTypDict(
                    status_code=400,
                    success=False,
                    msg="Error : Recovering distributor",
                    description="Invalid user input"
                )
            )
        
        return SuccessResponseTypDict(
            detail=BaseResponseTypDict(
                status_code=200,
                success=True,
                msg="Distributor recovered successfully"
            )
        )
        
    @catch_errors
    async def get(self,offset:int=1,limit:int=10,query:str=''):
        return await DistributorService(session=self.session,user_role=self.user_role).get(offset=offset,limit=limit,query=query)
        
    @catch_errors
    async def search(self,query:str):
        return await DistributorService(session=self.session,user_role=self.user_role).search(query=query)

    @catch_errors
    async def get_by_id(self,distributor_id:str):
        return await DistributorService(session=self.session,user_role=self.user_role).get_by_id(distributor_id=distributor_id)



