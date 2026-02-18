from sqlalchemy import String,Integer,Float,Boolean,Column,ForeignKey,Enum,ARRAY,func,TIMESTAMP,text,DateTime
from ..main import PG_BASE

class Users(PG_BASE):
    __tablename__="users"
    id=Column(String,primary_key=True)
    ui_id=Column(String,nullable=True)
    email=Column(String,nullable=False,unique=True)
    password=Column(String,nullable=False)
    name=Column(String,nullable=False)
    role=Column(String,nullable=False)
    tf_secret=Column(String,nullable=True)
    token_version=Column(Float)
    
    created_at=Column(TIMESTAMP(timezone=True),server_default=func.now())

    is_deleted=Column(Boolean,server_default=text("false"),default=False)
    deleted_by=Column(String)
    deleted_at=Column(DateTime(timezone=True),nullable=True)
