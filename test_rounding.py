import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

DATABASE_URL = 'postgresql+asyncpg://TibosCrmDatabase:AzureCRMDatabase#437734#1234#@tibos-crm-database.postgres.database.azure.com:5432/postgres?ssl=require'

async def main():
    engine = create_async_engine(DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession)
    async with async_session() as session:
        # Check orders with small pending dues
        res = await session.execute(text('''
            WITH invoice_stats AS (
                SELECT 
                    order_id,
                    COUNT(*) as total_invoices,
                    COUNT(*) FILTER (WHERE invoice_status = 'COMPLETED') as matching_invoices
                FROM orders_payment_invoice_info
                GROUP BY order_id
            ),
            order_calc AS (
                SELECT 
                    o.id as order_id,
                    o.ui_id,
                    c.owner,
                    COALESCE(CAST(o.unit_price AS Numeric), 0) * COALESCE(CAST(o.quantity AS Numeric), 0) - COALESCE(CAST(o.additional_discount AS Numeric), 0) + COALESCE(CAST(o.additional_price AS Numeric), 0) as customer_final_price,
                    ROUND((COALESCE(CAST(o.unit_price AS Numeric), 0) * COALESCE(CAST(o.quantity AS Numeric), 0) - COALESCE(CAST(o.additional_discount AS Numeric), 0) + COALESCE(CAST(o.additional_price AS Numeric), 0))::Numeric * 1.18) as customer_final_price_inc_gst,
                    s.total_invoices,
                    s.matching_invoices
                FROM orders o
                JOIN customers c ON o.customer_id = c.id
                JOIN invoice_stats s ON s.order_id = o.id
                WHERE o.is_deleted = false AND s.matching_invoices > 0
            )
            SELECT 
                oc.order_id,
                oc.ui_id,
                oc.owner,
                oc.customer_final_price,
                oc.customer_final_price_inc_gst,
                ROUND(oc.customer_final_price_inc_gst::Numeric / NULLIF(oc.total_invoices, 0)) as split_expected_amount_pg,
                i.payment_status,
                i.paid_amount,
                i.invoice_status
            FROM order_calc oc
            JOIN orders_payment_invoice_info i ON oc.order_id = i.order_id
            WHERE i.invoice_status = 'COMPLETED'
            AND i.payment_status IN ('NOT PAID', 'GST PENDING', 'HALF PAYMENT RECEIVED', 'SHORT PAYMENT RECEIVED', 'TDS PENDING')
        '''))
        rows = res.fetchall()
        
        pg_total = 0
        py_total = 0
        from decimal import Decimal, ROUND_HALF_UP
        
        for r in rows:
            pg_amt = max(float(r.split_expected_amount_pg) - float(r.paid_amount or 0), 0.0)
            pg_total += pg_amt
            
            # Python equivalent
            order_price_dec = Decimal(str(r.customer_final_price))
            cust_total_inc_gst = int((order_price_dec * Decimal('1.18')).quantize(Decimal('1'), rounding=ROUND_HALF_UP))
            py_split = int((Decimal(str(cust_total_inc_gst)) / Decimal(str(r.total_invoices))).quantize(Decimal('1'), rounding=ROUND_HALF_UP))
            py_amt = max(float(py_split) - float(r.paid_amount or 0), 0.0)
            py_total += py_amt
            
            if pg_amt != py_amt:
                print(f"Diff! Order {r.ui_id} ({r.owner}): PG={pg_amt}, PY={py_amt}")
                print(f"  customer_final_price: {r.customer_final_price}")
                print(f"  total_invoices: {r.total_invoices}")
                print(f"  paid_amount: {r.paid_amount}")
                
        print(f"PG Total: {pg_total}")
        print(f"PY Total: {py_total}")

asyncio.run(main())
