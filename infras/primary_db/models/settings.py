from sqlalchemy import String,Integer,Float,Boolean,Column,ForeignKey,Enum,BigInteger,Identity,func,TIMESTAMP,text,DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from ..main import PG_BASE

class Settings(PG_BASE):
    __tablename__="settings"
    id=Column(Integer,primary_key=True,autoincrement=True)
    name=Column(String,nullable=False,unique=True)
    datas=Column(JSONB,nullable=False)

    created_at=Column(TIMESTAMP(timezone=True),server_default=func.now())