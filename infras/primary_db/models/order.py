from sqlalchemy import String,Integer,Float,Boolean,Column,ForeignKey,ARRAY,BigInteger,Identity,func,TIMESTAMP,text,DateTime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from ..main import PG_BASE
from .customer import Customers


class Orders(PG_BASE):
    __tablename__="orders"
    id=Column(String,primary_key=True)
    ui_id=Column(String,nullable=True)
    sequence_id=Column(Integer,Identity(always=True),nullable=False)
    customer_id=Column(String,ForeignKey("customers.id"))
    distributor_id=Column(String,ForeignKey("distributors.id"),nullable=True)
    discount_id=Column(String,nullable=False)
    product_id=Column(String,ForeignKey("products.id",ondelete="CASCADE"))
    additional_price=Column(BigInteger,nullable=True)
    quantity=Column(Integer,nullable=False)
    activated=Column(Boolean,nullable=True)
    unit_price=Column(Float,nullable=True)
    delivery_info=Column(JSONB,nullable=False)
    logistic_info=Column(JSONB,nullable=False)
    vendor_commision=Column(String,nullable=True)
    additional_discount=Column(String,nullable=False)

    customer=relationship("Customers",back_populates="order")
    product=relationship("Products",back_populates="order")
    is_deleted=Column(Boolean,server_default=text("false"),nullable=False)
    deleted_by=Column(String,ForeignKey('users.id'))

    created_at=Column(TIMESTAMP(timezone=True),server_default=func.now())
    deleted_at=Column(DateTime(timezone=True),nullable=True)

    order_payment_invoice_info=relationship("OrdersPaymentInvoiceInfo",back_populates="order",cascade="all, delete-orphan")


class OrdersPaymentInvoiceInfo(PG_BASE):
    __tablename__="orders_payment_invoice_info"
    id=Column(BigInteger,primary_key=True,autoincrement=True)
    order_id=Column(String,ForeignKey("orders.id",ondelete="CASCADE"),nullable=False)
    payment_status=Column(String,nullable=True)
    invoice_status=Column(String,nullable=False)
    invoice_number=Column(String,nullable=True)
    invoice_date=Column(String,nullable=True)
    paid_amount=Column(BigInteger,nullable=True)

    order=relationship("Orders",back_populates='order_payment_invoice_info')