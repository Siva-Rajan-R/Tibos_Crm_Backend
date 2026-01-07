from enum import Enum

class UserRoles(Enum):
    ADMIN="admin".upper()
    SUPER_ADMIN='super admin'.upper()
    USER="user".upper()

class EnvironmentEnum(Enum):
    DEVELOPMENT="DEVELOPMENT"
    PRODUCTION="PRODUCTION"
    