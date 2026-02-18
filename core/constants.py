from core.data_formats.enums.user_enums import UserRoles
from typing import Optional,Dict

UI_ID_STARTING_DIGIT=100000
LUI_ID_CUSTOMER_PREFIX="CUST"
LUI_ID_CONTACT_PREFIX="CONTC"
LUI_ID_DISTRI_PREFIX="DIST"
LUI_ID_PRODUCT_PREFIX="PROD"
LUI_ID_LEAD_PREFIX="LEAD"
LUI_ID_OPPOR_PREFIX="OPPR"
LUI_ID_ORDER_PREFIX="ORD"
LUI_ID_USER_PREFIX="USR"
DEFAULT_GST="18%"
DEFAULT_ADDON_YEAR=365

ROLES_ALLOWED:Dict[str,Dict[str,set|None]]={
    UserRoles.ADMIN.value:{
        'user':None,
        'recyclebin':None
    },
    UserRoles.SUPER_ADMIN.value:{},
    UserRoles.USER.value:{
        'user':None,
        'recyclebin':None,
        'product':{'GET'},
        'contact':{'GET'},
        'customer':{'GET'},
        'order':{'GET'},
        'lead':{'GET'},
        'opportunities':{'GET'}
    }
}