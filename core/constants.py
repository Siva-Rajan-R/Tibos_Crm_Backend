from core.data_formats.enums.common_enums import UserRoles
from typing import Optional,Dict

UI_ID_STARTING_DIGIT=100000

ROLES_ALLOWED:Dict[str,Dict[str,set|None]]={
    UserRoles.ADMIN.value:{
        'user':None
    },
    UserRoles.SUPER_ADMIN.value:{},
    UserRoles.USER.value:{
        'user':None,
        'product':{'GET'},
        'contact':{'GET'},
        'customer':{'GET'},
        'order':{'GET'},
        'lead':{'GET'},
        'opportunities':{'GET'}
    }
}