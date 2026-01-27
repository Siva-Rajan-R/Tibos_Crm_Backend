from infras.primary_db.services.product_service import ProductsService
from core.utils.uuid_generator import generate_uuid
from sqlalchemy import select,delete,update,or_,cast,String,func,Float
from sqlalchemy.ext.asyncio import AsyncSession
from icecream import ic
from core.data_formats.enums.common_enums import UserRoles
from core.decorators.error_handler_dec import catch_errors
from schemas.db_schemas.product import AddProductDbSchema,UpdateProductDbSchema
from schemas.request_schemas.product import AddProductSchema,UpdateProductSchema,RecoverProductSchema
from math import ceil
from . import HTTPException,ErrorResponseTypDict,SuccessResponseTypDict,BaseResponseTypDict
from core.utils.excel_data_extractor import extract_excel_data
from models.import_export_models.excel_headings_mapper import PRODUCTS_MAPPER
from fastapi import UploadFile
from core.data_formats.enums.common_enums import ImportExportTypeEnum


class HandleProductsRequest:
    def __init__(self,session:AsyncSession,user_role:UserRoles,cur_user_id:str):
        self.session=session
        self.user_role=user_role
        self.cur_user_id=cur_user_id

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
                ).model_dump(mode='json')
            )
        
    @catch_errors
    async def add(self,data:AddProductSchema):
        res=await ProductsService(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).add(data=data)
        if not res or isinstance(res,ErrorResponseTypDict):
            detail:ErrorResponseTypDict=ErrorResponseTypDict(
                    status_code=400,
                    msg="Error : Creating Product",
                    description="A Unknown Error, Please Try Again Later!"
                ) if not isinstance(res,ErrorResponseTypDict) else res
            
            raise HTTPException(
                status_code=detail.status_code,
                detail=detail.model_dump(mode='json')
            )
        return SuccessResponseTypDict(
            detail=BaseResponseTypDict(
                status_code=200,
                success=True,
                msg="Product created successfully"
            )
        )
    
    @catch_errors
    async def add_bulk(self,type:ImportExportTypeEnum,file:UploadFile):

        if type.value==ImportExportTypeEnum.EXCEL.value:
            datas=extract_excel_data(excel_file=file.file,headings_mapper=PRODUCTS_MAPPER)
            if not datas or len(datas)<=0:
                raise HTTPException(
                    status_code=400,
                    detail=ErrorResponseTypDict(
                        status_code=400,
                        success=False,
                        msg="Adding bulk products",
                        description="Invalid columns or insufficent datas to add"
                    ).model_dump(mode='json')
                )
            res= await ProductsService(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).add_bulk(datas=datas)
            if res:
                return SuccessResponseTypDict(
                    detail=BaseResponseTypDict(
                        status_code=200,
                        success=True,
                        msg="Products added successfully"
                    )
                )

        detail:ErrorResponseTypDict=ErrorResponseTypDict(
                status_code=400,
                msg="Error : Creating Contact",
                description="A Unknown Error, Please Try Again Later!"
            ) if not isinstance(res,ErrorResponseTypDict) else res
        
        raise HTTPException(
            status_code=detail.status_code,
            detail=detail.model_dump(mode='json')
        )


    @catch_errors   
    async def update(self,data:UpdateProductDbSchema):
        res = await ProductsService(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).update(data=data)
        if not res or isinstance(res,ErrorResponseTypDict):
            detail:ErrorResponseTypDict=ErrorResponseTypDict(
                    status_code=400,
                    msg="Error : Updating Product",
                    description="A Unknown Error, Please Try Again Later!"
                ) if not isinstance(res,ErrorResponseTypDict) else res
            
            raise HTTPException(
                status_code=detail.status_code,
                detail=detail.model_dump(mode='json')
            )
        
        return SuccessResponseTypDict(
            detail=BaseResponseTypDict(
                status_code=200,
                success=True,
                msg="Product updated successfully"
            )
        )


    @catch_errors
    async def delete(self,product_id:str,soft_delete:bool=True):
        res = await ProductsService(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).delete(product_id=product_id,soft_delete=soft_delete)
        if not res or isinstance(res,ErrorResponseTypDict):
            detail:ErrorResponseTypDict=ErrorResponseTypDict(
                    status_code=400,
                    msg="Error : Deleting Product",
                    description="A Unknown Error, Please Try Again Later!"
                ) if not isinstance(res,ErrorResponseTypDict) else res
            
            raise HTTPException(
                status_code=detail.status_code,
                detail=detail.model_dump(mode='json')
            )
        
        return SuccessResponseTypDict(
            detail=BaseResponseTypDict(
                status_code=200,
                success=True,
                msg="Product deleted successfully"
            )
        )
    
    @catch_errors  
    async def recover(self,data:RecoverProductSchema):
        res = await ProductsService(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).recover(product_torecover=data.product_id)
        if not res or isinstance(res,ErrorResponseTypDict):
            detail:ErrorResponseTypDict=ErrorResponseTypDict(
                    status_code=400,
                    msg="Error : Recovering Product",
                    description="A Unknown Error, Please Try Again Later!"
                ) if not isinstance(res,ErrorResponseTypDict) else res
            
            raise HTTPException(
                status_code=detail.status_code,
                detail=detail.model_dump(mode='json')
            )
        
        return SuccessResponseTypDict(
            detail=BaseResponseTypDict(
                status_code=200,
                success=True,
                msg="Product recovered successfully"
            )
        )   

    @catch_errors   
    async def get(self,offset:int=1,limit:int=10,query:str=''):
        return await ProductsService(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).get(offset=offset,limit=limit,query=query)
    
    @catch_errors
    async def search(self, query: str):
        return await ProductsService(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).search(query=query)
    
    @catch_errors
    async def get_by_id(self,product_id:str):
        return await ProductsService(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).get_by_id(product_id=product_id)



