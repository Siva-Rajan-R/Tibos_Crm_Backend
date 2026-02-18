from infras.primary_db.services.distri_service import DistributorService
from core.utils.uuid_generator import generate_uuid
from sqlalchemy import select,delete,update,or_,func,String
from sqlalchemy.ext.asyncio import AsyncSession
from icecream import ic
from core.data_formats.enums.user_enums import UserRoles
from pydantic import EmailStr
from typing import Optional,List
from schemas.db_schemas.customer import AddCustomerDbSchema,UpdateCustomerDbSchema
from schemas.request_schemas.distributor import CreateDistriSchema,UpdateDistriSchema,RecoverDistriSchema
from core.decorators.error_handler_dec import catch_errors
from math import ceil
from . import HTTPException,ErrorResponseTypDict,SuccessResponseTypDict,BaseResponseTypDict
from core.utils.discount_validator import validate_discount
from fastapi import UploadFile
from core.utils.excel_data_extractor import extract_excel_data
from core.data_formats.enums.dd_enums import ImportExportTypeEnum
from models.import_export_models.excel_headings_mapper import DISTRI_MAPPER



class HandleDistributorRequest:
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
    async def add(self,data:CreateDistriSchema):
        if validate_discount(data.discount) is None:
            raise HTTPException(
                status_code=400,
                detail=ErrorResponseTypDict(
                    status_code=400,
                    description="Invalid Data format for discount",
                    msg="Error : Adding Distributor",
                    success=False
                ).model_dump(mode='json')
            )

        res = await DistributorService(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).add(data=data)
        if not res or isinstance(res,ErrorResponseTypDict):
            detail:ErrorResponseTypDict=ErrorResponseTypDict(
                    status_code=400,
                    msg="Error : Creating Distributor",
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
                msg="Distributor created successfully"
            )
        )
    
    @catch_errors
    async def add_bulk(self,type:ImportExportTypeEnum,file:UploadFile):
        if type.value==ImportExportTypeEnum.EXCEL.value:
            datas_toadd=extract_excel_data(excel_file=file.file,headings_mapper=DISTRI_MAPPER)
            if not datas_toadd or len(datas_toadd)<=0:
                raise HTTPException(
                    status_code=400,
                    detail=ErrorResponseTypDict(
                        status_code=400,
                        success=False,
                        msg="Adding bulk distributor",
                        description="Invalid columns or insufficent datas to add"
                    ).model_dump(mode='json')
                )
            res=await DistributorService(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).add_bulk(datas=datas_toadd)
            if res:
                return SuccessResponseTypDict(
                    detail=BaseResponseTypDict(
                        status_code=200,
                        msg="Distributor added successfully",
                        success=True
                    )
                )
            
        detail:ErrorResponseTypDict=ErrorResponseTypDict(
                status_code=400,
                msg="Error : Creating Distributors",
                description="A Unknown Error, Please Try Again Later!",
                success=False
            ) if not isinstance(res,ErrorResponseTypDict) else res
        
        raise HTTPException(
            status_code=detail.status_code,
            detail=detail.model_dump(mode='json')
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
                ).model_dump(mode='json')
            )
        
        res=await DistributorService(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).update(data=data)
        if not res or isinstance(res,ErrorResponseTypDict):
            detail:ErrorResponseTypDict=ErrorResponseTypDict(
                    status_code=400,
                    msg="Error : Update Distributor",
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
                msg="Distributor updated successfully"
            )
        )
        
    @catch_errors
    async def delete(self,distributor_id:str,soft_delete:bool=True):
        res=await DistributorService(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).delete(distributor_id=distributor_id,soft_delete=soft_delete)
        if not res or isinstance(res,ErrorResponseTypDict):
            detail:ErrorResponseTypDict=ErrorResponseTypDict(
                    status_code=400,
                    msg="Error : Deleting Distributor",
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
                msg="Distributor deleted successfully"
            )
        )

    @catch_errors
    async def recover(self,data:RecoverDistriSchema):
        res=await DistributorService(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).recover(distributor_id=data.distributor_id)
        if not res or isinstance(res,ErrorResponseTypDict):
            detail:ErrorResponseTypDict=ErrorResponseTypDict(
                    status_code=400,
                    msg="Error : Recovering Distributor",
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
                msg="Distributor recovered successfully"
            )
        )
        
    @catch_errors
    async def get(self,cursor:int=1,limit:int=10,query:str=''):
        if cursor is None:
            raise HTTPException(
                status_code=400,
                detail=ErrorResponseTypDict(
                    status_code=400,
                    description="No more datas found for distributor",
                    msg="Error : fetching distributor",
                    success=False
                )
            )
        return await DistributorService(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).get(cursor=cursor,limit=limit,query=query)
        
    @catch_errors
    async def search(self,query:str):
        return await DistributorService(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).search(query=query)

    @catch_errors
    async def get_by_id(self,distributor_id:str):
        return await DistributorService(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).get_by_id(distributor_id=distributor_id)



