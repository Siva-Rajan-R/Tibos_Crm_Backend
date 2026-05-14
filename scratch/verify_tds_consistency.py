
def simulate_breakdown(invoices, total_price):
    num_invoices = len(invoices)
    expected_per_invoice = total_price / num_invoices
    
    # Categories counts and paid sums
    categories = {
        "NOT PAID": {"count": 0, "paid": 0},
        "GST PENDING": {"count": 0, "paid": 0},
        "HALF PENDING": {"count": 0, "paid": 0},
        "SHORT PENDING": {"count": 0, "paid": 0},
        "TDS PENDING": {"count": 0, "paid": 0}
    }
    
    completed_pending_count = 0
    completed_pending_paid = 0
    
    for inv in invoices:
        status = inv["status"]
        paid = inv["paid"]
        
        if inv["invoice_status"] == "COMPLETED":
            if status not in ["PAID", "FULL PAYMENT RECEIVED"]:
                completed_pending_count += 1
                completed_pending_paid += paid
                
                if status in categories:
                    categories[status]["count"] += 1
                    categories[status]["paid"] += paid

    pending_amount_expr = completed_pending_count * expected_per_invoice - completed_pending_paid
    
    # NEW LOGIC: Explicit category amounts
    results = {}
    for cat, data in categories.items():
        results[cat] = round(data["count"] * expected_per_invoice - data["paid"])
    
    return {
        "total_pending_expr": round(pending_amount_expr),
        "breakdown": results,
        "sum_of_breakdown": sum(results.values())
    }

def test_consistency():
    print("Testing scenario: 1 NOT PAID, 1 TDS PENDING, 1 GHOST (NULL status)")
    invoices = [
        {"status": "NOT PAID", "paid": 0, "invoice_status": "COMPLETED"},
        {"status": "TDS PENDING", "paid": 0, "invoice_status": "COMPLETED"},
        {"status": "NULL", "paid": 0, "invoice_status": "COMPLETED"} # Ghost
    ]
    total_price = 3000
    
    res = simulate_breakdown(invoices, total_price)
    print(f"Result: {res}")
    
    # In the old logic, TDS would be 2000 (1000 from TDS + 1000 from Ghost)
    # In the new logic, TDS should be 1000.
    assert res["breakdown"]["TDS PENDING"] == 1000, f"Expected 1000 TDS, got {res['breakdown']['TDS PENDING']}"
    assert res["breakdown"]["NOT PAID"] == 1000
    
    print("SUCCESS: TDS total only includes TDS invoices. Ghost money is excluded from the breakdown categories.")

if __name__ == "__main__":
    test_consistency()
