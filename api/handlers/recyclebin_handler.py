from infras.primary_db.services import customer_service,contact_service,user_service,product_service,lead_service,opportunity_service,distri_service,order_service,distributor_payment_service
from sqlalchemy.ext.asyncio import AsyncSession
from core.data_formats.enums.user_enums import UserRoles
from schemas.request_schemas.order import OrderFilterSchema
class HandleRecycleBinRequests:
    def __init__(self,session:AsyncSession):
        self.session=session

    async def get(self, cursor: int = 1, limit: int = 10):
        user_role=UserRoles.SUPER_ADMIN
        customers=await customer_service.CustomersService(session=self.session,user_role=user_role,cur_user_id='').get(include_deleted=True,cursor=cursor,limit=limit)
        contacts=await contact_service.ContactsService(session=self.session,user_role=user_role,cur_user_id='').get(include_deleted=True,cursor=cursor,limit=limit)
        users=await user_service.UserService(session=self.session,user_role=user_role,cur_user_id='').get(include_deleted=True) if cursor == 1 else {'users': []}
        products=await product_service.ProductsService(session=self.session,user_role=user_role,cur_user_id='').get(include_deleted=True,cursor=cursor,limit=limit)
        leads=await lead_service.LeadsService(session=self.session,user_role=user_role,cur_user_id='').get(include_deleted=True,cursor=cursor,limit=limit)
        opportunities=await opportunity_service.OpportunitiesService(session=self.session,user_role=user_role,cur_user_id='').get(include_deleted=True,cursor=cursor,limit=limit)
        distributors=await distri_service.DistributorService(session=self.session,user_role=user_role,cur_user_id='').get(include_deleted=True,cursor=cursor,limit=limit)
        orders=await order_service.OrdersService(session=self.session,user_role=user_role,cur_user_id='').get(include_deleted=True,cursor=cursor,limit=limit,filter=OrderFilterSchema())
        distributor_payments=await distributor_payment_service.DistributorsPaymentsService(session=self.session,user_role=user_role,cur_user_id='').get(include_deleted=True,cursor=cursor,limit=limit)

        return [
            {
                'customers':customers['customers'],
                'contacts':contacts['contacts'],
                'users':users['users'],
                'products':products['products'],
                'leads':leads['leads'],
                'opportunities':opportunities['opportunities'],
                'distributors':distributors['distributors'],
                'orders':orders['orders'],
                'distributor_payments':distributor_payments['distributors_payments']
            }
        ]
