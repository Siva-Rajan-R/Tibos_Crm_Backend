from sqlalchemy import String,Integer,Float,Boolean,Column,ForeignKey,ARRAY,BigInteger,Identity,func,TIMESTAMP,text,DateTime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from ..main import PG_BASE


class Distributors(PG_BASE):
    __tablename__="distributors"
    id=Column(String,primary_key=True)
    sequence_id=Column(BigInteger,Identity(always=True),nullable=False)
    name=Column(String,nullable=False)
    product_id=Column(String,ForeignKey('products.id'),nullable=False)
    discount=Column(String,nullable=False)
    created_at=Column(TIMESTAMP(timezone=True),server_default=func.now())
    is_deleted=Column(Boolean,server_default=text("false"),nullable=False)
    deleted_by=Column(String,ForeignKey('users.id'))
    deleted_at=Column(DateTime(timezone=True),nullable=True)