from sqlalchemy import String,Integer,Float,Boolean,Column,ForeignKey,Enum,ARRAY
from sqlalchemy.orm import relationship
from database.configs.pg_config import PG_BASE
from data_formats.enums.pg_enums import ProductTypes


class Products(PG_BASE):
    __tablename__="products"
    id=Column(String,primary_key=True)
    name=Column(String,nullable=False)
    description=Column(String,nullable=False)
    price=Column(Float,nullable=False)
    available_qty=Column(Integer,nullable=False)
    product_type=Column(Enum(ProductTypes),nullable=False)

    order=relationship("Orders",back_populates="product",cascade="all, delete-orphan")