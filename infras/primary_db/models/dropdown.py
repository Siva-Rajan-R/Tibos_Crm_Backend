from sqlalchemy import String,Integer,Float,Boolean,Column,ForeignKey,ARRAY,BigInteger,Identity,func,TIMESTAMP,text,DateTime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from ..main import PG_BASE


class DropDownValues(PG_BASE):
    __tablename__="dropdown_values"
    id=Column(Integer,primary_key=True,autoincrement=True)
    name=Column(String,unique=True)
    values=Column(JSONB)