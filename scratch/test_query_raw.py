import asyncio
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, func, cast, Numeric, Date, and_
from core.settings import SETTINGS
import datetime

from infras.primary_db.models.order import Orders, OrdersPaymentInvoiceInfo
from infras.primary_db.models.customer import Customers
from infras.primary_db.models.contact import Contacts
from infras.primary_db.models.distributor import Distributors
from infras.primary_db.models.product import Products
from infras.primary_db.calculations import customer_final_price_inc_gst
from core.data_formats.enums.order_enums import InvoiceStatus, PaymentStatus

async def main():
    engine = create_async_engine(SETTINGS.PG_DB_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        from_date = datetime.date(2000, 1, 1)
        to_date = datetime.date(2030, 1, 1)
        
        invoice_stats_subq = (
            select(
                OrdersPaymentInvoiceInfo.order_id,
                func.count().label("total_invoices"),
                func.count().filter(
                    and_(
                        OrdersPaymentInvoiceInfo.invoice_status == InvoiceStatus.COMPLETED.value,
                        OrdersPaymentInvoiceInfo.payment_status.notin_([
                            PaymentStatus.PAID.value,
                            PaymentStatus.FULL_PAYMENT_RECEIVED.value
                        ])
                    )
                ).label("matching_invoices")
            )
            .group_by(OrdersPaymentInvoiceInfo.order_id)
            .subquery()
        )
        
        invoice_total_value = func.round(
            cast(customer_final_price_inc_gst, Numeric) / func.nullif(invoice_stats_subq.c.matching_invoices, 1)
        )
        
        split_expected_amount = func.round(
            cast(customer_final_price_inc_gst, Numeric) / func.nullif(invoice_stats_subq.c.total_invoices, 1)
        )
        invoice_pending_value = func.greatest(
            split_expected_amount - func.coalesce(OrdersPaymentInvoiceInfo.paid_amount, 0),
            0
        )
        
        stmt = (
            select(
                Orders.id.label("order_id"),
                OrdersPaymentInvoiceInfo.id.label("invoice_id"),
                invoice_stats_subq.c.matching_invoices,
                invoice_stats_subq.c.total_invoices,
                customer_final_price_inc_gst.label("gst_amount"),
                invoice_total_value.label("inv_val"),
                invoice_pending_value.label("pend_val")
            )
            .select_from(Orders)
            .join(OrdersPaymentInvoiceInfo, OrdersPaymentInvoiceInfo.order_id == Orders.id)
            .join(invoice_stats_subq, invoice_stats_subq.c.order_id == Orders.id)
            .join(Products, Products.id == Orders.product_id, isouter=True)
            .join(Customers, Customers.id == Orders.customer_id, isouter=True)
            .where(
                OrdersPaymentInvoiceInfo.invoice_status == InvoiceStatus.COMPLETED.value,
                OrdersPaymentInvoiceInfo.payment_status.notin_([
                    PaymentStatus.PAID.value,
                    PaymentStatus.FULL_PAYMENT_RECEIVED.value
                ]),
                Customers.owner == "NAGARAJ D"
            )
        )
        
        rows = (await session.execute(stmt)).mappings().all()
        for r in rows:
            print(dict(r))

if __name__ == "__main__":
    asyncio.run(main())
