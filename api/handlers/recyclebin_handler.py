from infras.primary_db.services import customer_service,contact_service,user_service,product_service,lead_service,opportunity_service,distri_service,order_service
from sqlalchemy.ext.asyncio import AsyncSession
from core.data_formats.enums.common_enums import UserRoles

class HandleRecycleBinRequests:
    def __init__(self,session:AsyncSession):
        self.session=session

    async def get(self):
        user_role=UserRoles.SUPER_ADMIN
        offset=1
        limit=10
        customers=await customer_service.CustomersService(session=self.session,user_role=user_role,cur_user_id='').get(include_deleted=True)
        contacts=await contact_service.ContactsService(session=self.session,user_role=user_role,cur_user_id='').get(include_deleted=True,offset=offset,limit=limit)
        users=await user_service.UserService(session=self.session,user_role=user_role,cur_user_id='').get(include_deleted=True)
        products=await product_service.ProductsService(session=self.session,user_role=user_role,cur_user_id='').get(include_deleted=True)
        leads=await lead_service.LeadsService(session=self.session,user_role=user_role,cur_user_id='').get(include_deleted=True)
        opportunities=await opportunity_service.OpportunitiesService(session=self.session,user_role=user_role,cur_user_id='').get(include_deleted=True)
        distributors=await distri_service.DistributorService(session=self.session,user_role=user_role,cur_user_id='').get(include_deleted=True)
        orders=await order_service.OrdersService(session=self.session,user_role=user_role,cur_user_id='').get(include_deleted=True)

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
