
def test_calculation():
    # Data for the example from Image 1:
    # Order Total with GST = 5900
    # Number of Invoices = 12
    # Total Paid = 736 (491 + 245)
    
    customer_amount_with_gst_val = 5900
    paid_total = 736
    
    total_invoices = 12
    
    # Counts and Paid sums per status
    # TDS Pending: Invoice #1, Paid 491
    tds_pendings = 1
    tds_paid_sum = 491
    
    # Half Payment Received: Invoice #2, Paid 245
    half_pendings = 1
    half_paid_sum = 245
    
    # Not Paid: Invoices #3-12, Paid 0
    not_paid_pendings = 10
    not_paid_paid_sum = 0
    
    pending_amount_expr = max(customer_amount_with_gst_val - paid_total, 0) # 5164
    
    print(f"Total Pending: {pending_amount_expr}")
    
    # Current logic (conceptual):
    tds_pending_amount_current = pending_amount_expr if tds_pendings > 0 else 0
    half_pending_amount_current = pending_amount_expr if half_pendings > 0 else 0
    not_paid_amount_current = pending_amount_expr if not_paid_pendings > 0 else 0
    
    print(f"\nCurrent Logic (Incorrect):")
    print(f"TDS Amount: {tds_pending_amount_current}")
    print(f"Half Amount: {half_pending_amount_current}")
    print(f"Not Paid Amount: {not_paid_amount_current}")
    print(f"Sum of parts: {tds_pending_amount_current + half_pending_amount_current + not_paid_amount_current}")
    
    # Proposed logic:
    expected_invoice_amount = customer_amount_with_gst_val / total_invoices
    
    # Calculate each part and round
    tds_pending_amount_new = round(tds_pendings * expected_invoice_amount - tds_paid_sum)
    half_pending_amount_new = round(half_pendings * expected_invoice_amount - half_paid_sum)
    not_paid_amount_new = round(not_paid_pendings * expected_invoice_amount - not_paid_paid_sum)
    
    # Adjust last part to ensure exact sum if needed (though rounding usually works)
    sum_new = tds_pending_amount_new + half_pending_amount_new + not_paid_amount_new
    
    print(f"\nProposed Logic:")
    print(f"Expected Invoice Amount: {expected_invoice_amount:.2f}")
    print(f"TDS Amount: {tds_pending_amount_new}")
    print(f"Half Amount: {half_pending_amount_new}")
    print(f"Not Paid Amount: {not_paid_amount_new}")
    print(f"Sum of parts: {sum_new}")
    print(f"Matches Total? {sum_new == pending_amount_expr}")

if __name__ == "__main__":
    test_calculation()
