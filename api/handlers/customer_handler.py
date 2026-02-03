from infras.primary_db.services.customer_service import CustomersService
from core.utils.uuid_generator import generate_uuid
from infras.primary_db.models.order import Orders
from sqlalchemy import select,delete,update,or_,func,String
from sqlalchemy.ext.asyncio import AsyncSession
from icecream import ic
from core.data_formats.enums.common_enums import UserRoles
from pydantic import EmailStr
from typing import Optional,List
from schemas.db_schemas.customer import AddCustomerDbSchema,UpdateCustomerDbSchema
from schemas.request_schemas.customer import AddCustomerSchema,UpdateCustomerSchema,RecoverCustomerSchema
from core.decorators.error_handler_dec import catch_errors
from math import ceil
from . import HTTPException,ErrorResponseTypDict,SuccessResponseTypDict,BaseResponseTypDict
from core.utils.mob_no_validator import mobile_number_validator
from core.utils.excel_data_extractor import extract_excel_data
from models.import_export_models.excel_headings_mapper import ACCOUNTS_MAPPER
from fastapi import UploadFile
from core.data_formats.enums.common_enums import ImportExportTypeEnum


class HandleCustomersRequest:
    def __init__(self,session:AsyncSession,user_role:UserRoles,cur_user_id:str):
        self.session=session
        self.user_role=user_role
        self.cur_user_id=cur_user_id

        # if isinstance(self.user_role,UserRoles):
        #     self.user_role=self.user_role.value

        # if self.user_role==UserRoles.USER.value:
        #     raise HTTPException(
        #         status_code=401,
        #         detail=ErrorResponseTypDict(
        #             msg="Error : ",
        #             description="Insufficient permission",
        #             status_code=401,
        #             success=False
        #         ).model_dump(mode='json')
        #     )
       
    @catch_errors
    async def add(self,data:AddCustomerSchema):
        if not mobile_number_validator(mob_no=data.mobile_number):
            raise HTTPException(
                status_code=400,
                detail=ErrorResponseTypDict(
                    status_code=400,
                    success=False,
                    msg="Error : Creating customer ",
                    description="Invalid input data, May be its a mobile number"
                ).model_dump(mode='json')
            )
        res = await CustomersService(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).add(data=data)
        if not res or isinstance(res,ErrorResponseTypDict):
            detail:ErrorResponseTypDict=ErrorResponseTypDict(
                    status_code=400,
                    msg="Error : Creating Customer",
                    description="A Unknown Error, Please Try Again Later!",
                    success=False
                ) if not isinstance(res,ErrorResponseTypDict) else res
            
            raise HTTPException(
                status_code=detail.status_code,
                detail=detail.model_dump(mode='json')
            )
        
        return SuccessResponseTypDict(
            detail=BaseResponseTypDict(
                status_code=200,
                success=True,
                msg="Customer created successfully"
            )
        )
    

    @catch_errors
    async def add_bulk(self,type:ImportExportTypeEnum,file:UploadFile):
        if type.value==ImportExportTypeEnum.EXCEL.value:
            datas_toadd=extract_excel_data(excel_file=file.file,headings_mapper=ACCOUNTS_MAPPER)
            if not datas_toadd or len(datas_toadd)<=0:
                raise HTTPException(
                    status_code=400,
                    detail=ErrorResponseTypDict(
                        status_code=400,
                        success=False,
                        msg="Adding bulk products",
                        description="Invalid columns or insufficent datas to add"
                    ).model_dump(mode='json')
                )
            res=await CustomersService(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).add_bulk(datas=datas_toadd)
            if res:
                return SuccessResponseTypDict(
                    detail=BaseResponseTypDict(
                        status_code=200,
                        msg="Accounts added successfully",
                        success=True
                    )
                )
            
        detail:ErrorResponseTypDict=ErrorResponseTypDict(
                status_code=400,
                msg="Error : Creating Customers",
                description="A Unknown Error, Please Try Again Later!",
                success=False
            ) if not isinstance(res,ErrorResponseTypDict) else res
        
        raise HTTPException(
            status_code=detail.status_code,
            detail=detail.model_dump(mode='json')
        )


        
    @catch_errors  
    async def update(self,data:UpdateCustomerSchema):
        if data.mobile_number and not mobile_number_validator(mob_no=data.mobile_number):
            raise HTTPException(
                status_code=400,
                detail=ErrorResponseTypDict(
                    status_code=400,
                    success=False,
                    msg="Error : Creating customer ",
                    description="Invalid input data, May be its a mobile number"
                ).model_dump(mode='json')
            )
        
        res=await CustomersService(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).update(data=data)
        if not res or isinstance(res,ErrorResponseTypDict):
            detail:ErrorResponseTypDict=ErrorResponseTypDict(
                    status_code=400,
                    msg="Error : Update Customer",
                    description="A Unknown Error, Please Try Again Later!",
                    success=False
                ) if not isinstance(res,ErrorResponseTypDict) else res
            
            raise HTTPException(
                status_code=detail.status_code,
                detail=detail.model_dump(mode='json')
            )
        
        return SuccessResponseTypDict(
            detail=BaseResponseTypDict(
                status_code=200,
                success=True,
                msg="Customer updated successfully"
            )
        )
        
    @catch_errors
    async def delete(self,customer_id:str,soft_delete:bool=True):
        res=await CustomersService(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).delete(customer_id=customer_id,soft_delete=soft_delete)
        if not res or isinstance(res,ErrorResponseTypDict):
            detail:ErrorResponseTypDict=ErrorResponseTypDict(
                    status_code=400,
                    msg="Error : Deleting Customer",
                    description="A Unknown Error, Please Try Again Later!",
                    success=False
                ) if not isinstance(res,ErrorResponseTypDict) else res
            
            raise HTTPException(
                status_code=detail.status_code,
                detail=detail.model_dump(mode='json')
            )
        
        return SuccessResponseTypDict(
            detail=BaseResponseTypDict(
                status_code=200,
                success=True,
                msg="Customer deleted successfully"
            )
        )
    
    @catch_errors  
    async def recover(self,data:RecoverCustomerSchema):    
        res=await CustomersService(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).recover(customer_id=data.customer_id)
        if not res or isinstance(res,ErrorResponseTypDict):
            detail:ErrorResponseTypDict=ErrorResponseTypDict(
                    status_code=400,
                    msg="Error : Recovering Customer",
                    description="A Unknown Error, Please Try Again Later!",
                    success=False
                ) if not isinstance(res,ErrorResponseTypDict) else res
            
            raise HTTPException(
                status_code=detail.status_code,
                detail=detail.model_dump(mode='json')
            )
        
        return SuccessResponseTypDict(
            detail=BaseResponseTypDict(
                status_code=200,
                success=True,
                msg="Customer recovered successfully"
            )
        )
        
    @catch_errors
    async def get(self,offset:int=1,limit:int=10,query:str=''):
        return await CustomersService(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).get(offset=offset,limit=limit,query=query)
        
    @catch_errors
    async def search(self,query:str):
        return await CustomersService(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).search(query=query)

    @catch_errors
    async def get_by_id(self,customer_id:str):
        return await CustomersService(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).get_by_id(customer_id=customer_id)



