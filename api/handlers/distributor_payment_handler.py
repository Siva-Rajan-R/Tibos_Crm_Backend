from infras.primary_db.services.distributor_payment_service import DistributorsPaymentsService
from sqlalchemy import select,delete,update,or_,func,String
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.exceptions import HTTPException
from icecream import ic
from pydantic import EmailStr
from typing import Optional,List
from core.data_formats.enums.user_enums import UserRoles
from schemas.request_schemas.distributor_payment import AddDistributorPaymentSchema,UpdateDistributorPaymentSchema
from core.decorators.db_session_handler_dec import start_db_transaction
from math import ceil
from models.response_models.req_res_models import SuccessResponseTypDict,BaseResponseTypDict,ErrorResponseTypDict


class HandleDistributorPaymentRequest:
    def __init__(self,session:AsyncSession,user_role:UserRoles,cur_user_id:str):
        self.session=session
        self.user_role=user_role
        self.cur_user_id=cur_user_id

        
    async def add(self,data:AddDistributorPaymentSchema):
        # if len(data.payment_infos)>12:
        #     raise HTTPException(
        #         status_code=400,
        #         detail=ErrorResponseTypDict(
        #             status_code=400,
        #             success=False,
        #             msg="Error : Creating Distributor payment",
        #             description="Payment infos length should be 12"
        #         )
        #     )
        res=await DistributorsPaymentsService(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).add(data=data)

        if res:
            return SuccessResponseTypDict(
                detail=BaseResponseTypDict(
                    status_code=200,
                    msg="Distributor Payment added successfully",
                    success=True
                )
            )
            
        detail:ErrorResponseTypDict=ErrorResponseTypDict(
                status_code=400,
                msg="Error : Creating Distributor payment",
                description="A Unknown Error, Please Try Again Later!",
                success=False
            ) if not isinstance(res,ErrorResponseTypDict) else res
        
        raise HTTPException(
            status_code=detail.status_code,
            detail=detail.model_dump(mode='json')
        )
         
    async def update(self,data:UpdateDistributorPaymentSchema):
        # if len(data.payment_infos)>12:
        #     raise HTTPException(
        #         status_code=400,
        #         detail=ErrorResponseTypDict(
        #             status_code=400,
        #             success=False,
        #             msg="Error : Creating Distributor payment",
        #             description="Payment infos length should be 12"
        #         )
        #     )
        
        res=await DistributorsPaymentsService(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).update(data=data)
        if res:
            return SuccessResponseTypDict(
                detail=BaseResponseTypDict(
                    status_code=200,
                    msg="Distributor Payment updated successfully",
                    success=True
                )
            )
            
        detail:ErrorResponseTypDict=ErrorResponseTypDict(
                status_code=400,
                msg="Error : Updating Distributor payment",
                description="A Unknown Error, Please Try Again Later!",
                success=False
            ) if not isinstance(res,ErrorResponseTypDict) else res
        
        raise HTTPException(
            status_code=detail.status_code,
            detail=detail.model_dump(mode='json')
        )
    

    async def delete(self,distri_payment_id:str,soft_delete:bool=True):
        res=await DistributorsPaymentsService(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).delete(distri_payment_id=distri_payment_id,soft_delete=soft_delete)
        if res:
            return SuccessResponseTypDict(
                detail=BaseResponseTypDict(
                    status_code=200,
                    msg="Distributor Payment deleted successfully",
                    success=True
                )
            )
            
        detail:ErrorResponseTypDict=ErrorResponseTypDict(
                status_code=400,
                msg="Error : Deleting Distributor payment",
                description="A Unknown Error, Please Try Again Later!",
                success=False
            ) if not isinstance(res,ErrorResponseTypDict) else res
        
        raise HTTPException(
            status_code=detail.status_code,
            detail=detail.model_dump(mode='json')
        )
        
    async def recover(self,distri_payment_id:str):
        res=await DistributorsPaymentsService(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).recover(distri_payment_id=distri_payment_id)
        if res:
            return SuccessResponseTypDict(
                detail=BaseResponseTypDict(
                    status_code=200,
                    msg="Distributor Payment recovered successfully",
                    success=True
                )
            )
            
        detail:ErrorResponseTypDict=ErrorResponseTypDict(
                status_code=400,
                msg="Error : Recovering Distributor payment",
                description="A Unknown Error, Please Try Again Later!",
                success=False
            ) if not isinstance(res,ErrorResponseTypDict) else res
        
        raise HTTPException(
            status_code=detail.status_code,
            detail=detail.model_dump(mode='json')
        )
    
    async def get(self,cursor:int=1,limit:int=50,query:str='',include_deleted:bool=False):
        res=await DistributorsPaymentsService(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).get(cursor=cursor,limit=limit,query=query,include_deleted=include_deleted)
        return res
        
    
    async def search(self,query:str):
        res=await DistributorsPaymentsService(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).search(query=query)
        return res

       
    async def get_by_id(self,distributor_payment_id:str):
        res=await DistributorsPaymentsService(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).get_by_id(distributor_payment_id=distributor_payment_id)
        return res


