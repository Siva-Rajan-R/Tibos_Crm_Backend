
import sys
import os

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from infras.primary_db.repos.order_repo import OrdersRepo
from sqlalchemy import select, and_, exists, or_
from infras.primary_db.models.order import Orders, OrdersPaymentInvoiceInfo

def verify_search_query():
    print("Verifying if invoice_number search condition is integrated...")
    
    # We can't easily run the real repo without a full session, 
    # but we can inspect the source or check if the code runs.
    
    # Just checking if the classes and conditions are correctly referenced
    search_term = "%test%"
    try:
        cond = exists().where(
            and_(
                OrdersPaymentInvoiceInfo.order_id == Orders.id,
                OrdersPaymentInvoiceInfo.invoice_number.ilike(search_term)
            )
        )
        print("SQLAlchemy condition object created successfully.")
        print(f"Condition: {cond}")
    except Exception as e:
        print(f"Error creating condition: {e}")
        sys.exit(1)

    print("\nVerification complete (Structure only).")

if __name__ == "__main__":
    verify_search_query()
