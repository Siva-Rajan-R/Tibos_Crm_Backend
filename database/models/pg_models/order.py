from sqlalchemy import String,Integer,Float,Boolean,Column,ForeignKey,Enum,ARRAY
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from database.configs.pg_config import PG_BASE
from data_formats.enums.pg_enums import InvoiceStatus,PaymentStatus


class Orders(PG_BASE):
    __tablename__="orders"
    id=Column(String,primary_key=True)
    customer_id=Column(String,ForeignKey("customers.id"))
    product_id=Column(String,ForeignKey("products.id",ondelete="CASCADE"))
    quantity=Column(Integer,nullable=False)
    total_price=Column(Float,nullable=False)
    discount_price=Column(Float,nullable=False)
    final_price=Column(Float,nullable=False)
    delivery_info=Column(JSONB,nullable=False)
    payment_status=Column(Enum(PaymentStatus),nullable=False)
    invoice_status=Column(Enum(InvoiceStatus),nullable=False)

    customer=relationship("Customers",back_populates="order")
    product=relationship("Products",back_populates="order")