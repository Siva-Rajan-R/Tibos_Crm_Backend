from sqlalchemy import String,Integer,Float,Boolean,Column,ForeignKey,ARRAY,BigInteger,Identity,func,TIMESTAMP
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from database.configs.pg_config import PG_BASE
from data_formats.enums.pg_enums import InvoiceStatus,PaymentStatus


class Orders(PG_BASE):
    __tablename__="orders"
    id=Column(String,primary_key=True)
    sequence_id=Column(Integer,Identity(always=True),nullable=False)
    customer_id=Column(String,ForeignKey("customers.id"))
    product_id=Column(String,ForeignKey("products.id",ondelete="CASCADE"))
    quantity=Column(Integer,nullable=False)
    total_price=Column(Float,nullable=False)
    discount_price=Column(Float,nullable=False)
    final_price=Column(Float,nullable=False)
    delivery_info=Column(JSONB,nullable=False)
    payment_status=Column(String,nullable=False)
    invoice_status=Column(String,nullable=False)

    customer=relationship("Customers",back_populates="order")
    product=relationship("Products",back_populates="order")

    created_at=Column(TIMESTAMP(timezone=True),server_default=func.now())