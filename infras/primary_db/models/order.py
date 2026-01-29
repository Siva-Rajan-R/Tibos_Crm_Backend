from sqlalchemy import String,Integer,Float,Boolean,Column,ForeignKey,ARRAY,BigInteger,Identity,func,TIMESTAMP,text,DateTime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from ..main import PG_BASE
from core.data_formats.enums.pg_enums import InvoiceStatus,PaymentStatus


class Orders(PG_BASE):
    __tablename__="orders"
    id=Column(String,primary_key=True)
    sequence_id=Column(Integer,Identity(always=True),nullable=False)
    customer_id=Column(String,ForeignKey("customers.id"))
    distributor_id=Column(String,ForeignKey("distributors.id"),nullable=True)
    product_id=Column(String,ForeignKey("products.id",ondelete="CASCADE"))
    quantity=Column(Integer,nullable=False)
    total_price=Column(Float,nullable=False)
    discount=Column(String,nullable=False)
    final_price=Column(Float,nullable=False)
    margin=Column(String,nullable=True)
    delivery_info=Column(JSONB,nullable=False)
    payment_status=Column(String,nullable=False)
    invoice_status=Column(String,nullable=False)
    invoice_number=Column(String,nullable=True)
    invoice_date=Column(String,nullable=True)
    purchase_type=Column(String,nullable=True)
    renewal_type=Column(String,nullable=True)


    customer=relationship("Customers",back_populates="order")
    product=relationship("Products",back_populates="order")
    is_deleted=Column(Boolean,server_default=text("false"),nullable=False)
    deleted_by=Column(String,ForeignKey('users.id'))

    created_at=Column(TIMESTAMP(timezone=True),server_default=func.now())
    deleted_at=Column(DateTime(timezone=True),nullable=True)