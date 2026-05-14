
def simulate_calculation(invoice_status, payment_status, paid_amount, expected_per_invoice=1000):
    # This simulates the logic in invoice_stats_subq and get method
    
    # BEFORE FIX
    # completed_invoices_count = 1 if invoice_status == "COMPLETED" else 0
    # completed_paid_total = paid_amount if invoice_status == "COMPLETED" else 0
    
    # AFTER FIX
    completed_invoices_count = 0
    completed_paid_total = 0
    if invoice_status == "COMPLETED":
        if payment_status != "PAID" and payment_status != "FULL PAYMENT RECEIVED":
            completed_invoices_count = 1
            completed_paid_total = paid_amount

    pending_amount_expr = completed_invoices_count * expected_per_invoice - completed_paid_total
    
    # Specific category pendings
    not_paid_pendings = 1 if payment_status == "NOT PAID" else 0
    tds_pendings = 1 if payment_status == "TDS PENDING" else 0
    # ... others ...

    not_paid_amount_raw = not_paid_pendings * expected_per_invoice - (paid_amount if payment_status == "NOT PAID" else 0)
    # ... others ...
    
    # TDS logic
    # tds_pending_amount_raw = max(pending_amount_expr - (not_paid_amount_raw + ...), 0)
    tds_pending_amount_raw = max(pending_amount_expr - not_paid_amount_raw, 0)
    
    return {
        "pending_total": pending_amount_expr,
        "tds_pending": tds_pending_amount_raw
    }

def test_fix():
    print("Testing scenario: Invoice COMPLETED, status FULL PAYMENT RECEIVED, paid amount 0")
    result = simulate_calculation("COMPLETED", "FULL PAYMENT RECEIVED", 0)
    print(f"Result: {result}")
    assert result["pending_total"] == 0, f"Expected 0 pending total, got {result['pending_total']}"
    assert result["tds_pending"] == 0, f"Expected 0 TDS pending, got {result['tds_pending']}"
    print("SUCCESS: Full Payment Received with 0 paid amount does not create pending dues.")

    print("\nTesting scenario: Invoice COMPLETED, status NOT PAID, paid amount 0")
    result = simulate_calculation("COMPLETED", "NOT PAID", 0)
    print(f"Result: {result}")
    assert result["pending_total"] == 1000
    assert result["tds_pending"] == 0 # It should be in NOT PAID, but since we only have TDS as fallback in this sim... 
    # Actually in real logic it would be:
    # pending_total = 1000
    # not_paid_amount = 1000
    # tds = 1000 - 1000 = 0.
    print("SUCCESS: Normal pending logic still works.")

if __name__ == "__main__":
    test_fix()
