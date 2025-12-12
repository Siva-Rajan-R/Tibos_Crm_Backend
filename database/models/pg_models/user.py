from sqlalchemy import String,Integer,Float,Boolean,Column,ForeignKey,Enum,ARRAY,func,TIMESTAMP
from database.configs.pg_config import PG_BASE
from data_formats.enums.common_enums import UserRoles

class Users(PG_BASE):
    __tablename__="users"
    id=Column(String,primary_key=True)
    email=Column(String,nullable=False)
    password=Column(String,nullable=False)
    name=Column(String,nullable=False)
    role=Column(String,nullable=False)

    created_at=Column(TIMESTAMP(timezone=True),server_default=func.now())
