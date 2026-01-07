from sqlalchemy import String,Integer,Float,Boolean,Column,ForeignKey,Enum,BigInteger,Identity,func,TIMESTAMP
from sqlalchemy.orm import relationship
from ..main import PG_BASE


class Contacts(PG_BASE):
    __tablename__="contacts"
    id=Column(String,primary_key=True)
    sequence_id=Column(Integer,Identity(always=True),nullable=False)
    customer_id=Column(String,ForeignKey("customers.id",ondelete="CASCADE"))
    name=Column(String,nullable=False)
    mobile_number=Column(String,nullable=False)
    email=Column(String,nullable=False)

    customer=relationship("Customers",back_populates="contact")

    created_at=Column(TIMESTAMP(timezone=True),server_default=func.now())