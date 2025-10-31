from sqlalchemy import String,Integer,Float,Boolean,Column,ForeignKey,Enum,ARRAY
from sqlalchemy.orm import relationship
from database.configs.pg_config import PG_BASE
from data_formats.enums.pg_enums import CustomerIndustries,CustomerSectors


class Customers(PG_BASE):
    __tablename__="customers"
    id=Column(String,primary_key=True)
    name=Column(String,nullable=False)
    mobile_number=Column(String,nullable=False)
    email=Column(String,nullable=False)
    website_url=Column(String,nullable=True)
    no_of_employee=Column(Integer,nullable=False)
    gst_number=Column(String,nullable=True)
    industry=Column(Enum(CustomerIndustries),nullable=False)
    sector=Column(Enum(CustomerSectors),nullable=False)
    primary_contact=Column(ARRAY(String),ForeignKey("contacts.id"))
    address=Column(String,nullable=True)

    contact=relationship("Contacts",back_populates="customer",cascade="all, delete-orphan")
    order=relationship("Orders",back_populates="customer")