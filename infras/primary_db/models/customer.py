from sqlalchemy import String,Integer,Float,Boolean,Column,ForeignKey,ARRAY,BigInteger,Identity,func,TIMESTAMP,text,DateTime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from ..main import PG_BASE


class Customers(PG_BASE):
    __tablename__="customers"
    id=Column(String,primary_key=True)
    ui_id=Column(String,nullable=True)
    sequence_id=Column(Integer,Identity(always=True),nullable=False)
    name=Column(String,nullable=False)
    mobile_number=Column(String,nullable=False)
    email=Column(String,nullable=False)
    website_url=Column(String,nullable=True)
    no_of_employee=Column(Integer,nullable=False)
    gst_number=Column(String,nullable=True)
    industry=Column(String,nullable=False)
    sector=Column(String,nullable=False)
    address=Column(JSONB,nullable=True)
    owner=Column(String,nullable=True)
    tenant_id=Column(String,nullable=True)

    created_at=Column(TIMESTAMP(timezone=True),server_default=func.now())

    is_deleted=Column(Boolean,server_default=text("false"),nullable=False)
    deleted_by=Column(String,ForeignKey('users.id'))
    deleted_at=Column(DateTime(timezone=True),nullable=True)

    contact=relationship("Contacts",back_populates="customer",cascade="all, delete-orphan")
    order=relationship("Orders",back_populates="customer")