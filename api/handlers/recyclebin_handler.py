from infras.primary_db.services import customer_service,contact_service,user_service,product_service,lead_service,opportunity_service,distri_service,order_service
from sqlalchemy.ext.asyncio import AsyncSession
from core.data_formats.enums.common_enums import UserRoles

class HandleRecycleBinRequests:
    def __init__(self,session:AsyncSession):
        self.session=session

    async def get(self):
        user_role=UserRoles.SUPER_ADMIN
        cursor=1
        limit=10
        customers=await customer_service.CustomersService(session=self.session,user_role=user_role,cur_user_id='').get(include_deleted=True)
        contacts=await contact_service.ContactsService(session=self.session,user_role=user_role,cur_user_id='').get(include_deleted=True,cursor=cursor,limit=limit)
        users=await user_service.UserService(session=self.session,user_role=user_role,cur_user_id='').get(include_deleted=True)
        products=await product_service.ProductsService(session=self.session,user_role=user_role,cur_user_id='').get(include_deleted=True,cursor=cursor)
        leads=await lead_service.LeadsService(session=self.session,user_role=user_role,cur_user_id='').get(include_deleted=True,cursor=cursor)
        opportunities=await opportunity_service.OpportunitiesService(session=self.session,user_role=user_role,cur_user_id='').get(include_deleted=True,cursor=cursor)
        distributors=await distri_service.DistributorService(session=self.session,user_role=user_role,cur_user_id='').get(include_deleted=True,cursor=cursor)
        orders=await order_service.OrdersService(session=self.session,user_role=user_role,cur_user_id='').get(include_deleted=True,cursor=cursor)

        return [
            {
                'customers':customers['customers'],
                'contacts':contacts['contacts'],
                'users':users['users'],
                'products':products['products'],
                'leads':leads['leads'],
                'opportunities':opportunities['opportunities'],
                'distributors':distributors['distributors'],
                'orders':orders['orders']
            }
        ]
