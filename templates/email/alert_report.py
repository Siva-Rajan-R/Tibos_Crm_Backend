"""
HTML email templates for alert and report emails.
Each function generates a self-contained HTML email body.
"""
from datetime import datetime


import os

FRONTEND_URL = os.getenv("FRONTEND_URL", "https://crm.tibostech.in")

def _currency(val) -> str:
    """Format number as Indian currency string without decimals (e.g. ₹1,47,76,639)."""
    try:
        val_float = float(val)
        is_negative = val_float < 0
        val_int = int(abs(round(val_float)))
        s = str(val_int)
        
        if len(s) > 3:
            last_3 = s[-3:]
            other = s[:-3]
            chunks = []
            while len(other) > 0:
                chunks.append(other[-2:])
                other = other[:-2]
            chunks.reverse()
            formatted = ",".join(chunks) + "," + last_3
        else:
            formatted = s
            
        result = f"₹{formatted}"
        return f"-{result}" if is_negative else result
    except (ValueError, TypeError):
        return "₹0"


def _base_style() -> str:
    return """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
        
        body { 
            margin: 0; 
            padding: 0; 
            background-color: #f1f5f9; 
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            -webkit-font-smoothing: antialiased;
        }
        .container { 
            max-width: 700px; 
            margin: 40px auto; 
            background: #ffffff; 
            border-radius: 16px; 
            box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.05), 0 8px 10px -6px rgba(0, 0, 0, 0.05);
            overflow: hidden; 
            border: 1px solid #e2e8f0;
        }
        .header { 
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); 
            color: #ffffff; 
            padding: 40px 48px; 
            text-align: left;
            position: relative;
        }
        .header::after {
            content: '';
            position: absolute;
            top: 0; right: 0; bottom: 0; left: 0;
            background: radial-gradient(circle at top right, rgba(59, 130, 246, 0.15), transparent);
        }
        .header h1 { 
            margin: 0; 
            font-size: 26px; 
            font-weight: 700; 
            letter-spacing: -0.025em;
            position: relative;
            z-index: 1;
        }
        .header p { 
            margin: 10px 0 0; 
            font-size: 14px; 
            color: #94a3b8; 
            line-height: 1.5;
            position: relative;
            z-index: 1;
        }
        .date-badge {
            display: inline-block;
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(4px);
            padding: 4px 12px;
            border-radius: 6px;
            font-size: 12px;
            color: #e2e8f0;
            margin-top: 12px;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        .body { padding: 40px 48px; }
        
        .section-header {
            display: flex;
            align-items: center;
            margin: 32px 0 16px;
        }
        .section-title { 
            font-size: 18px; 
            font-weight: 700; 
            color: #1e293b; 
            margin: 0;
            letter-spacing: -0.01em;
        }
        .section-divider {
            flex-grow: 1;
            height: 1px;
            background: #e2e8f0;
            margin-left: 16px;
        }

        /* Stats Grid */
        .stats-grid {
            display: table;
            width: 100%;
            border-spacing: 12px 0;
            margin: 0 -12px 24px;
        }
        .stat-card { 
            display: table-cell;
            background: #f8fafc; 
            border-radius: 12px; 
            padding: 20px; 
            text-align: left;
            border: 1px solid #f1f5f9;
            width: 50%;
        }
        .stat-card .value { 
            font-size: 24px; 
            font-weight: 700; 
            color: #0f172a; 
            display: block;
        }
        .stat-card .label { 
            font-size: 12px; 
            font-weight: 600;
            color: #64748b; 
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-top: 4px;
        }

        /* Tables */
        .table-container {
            background: #ffffff;
            border-radius: 12px;
            border: 1px solid #e2e8f0;
            overflow: hidden;
            margin: 16px 0;
        }
        table.report { 
            width: 100%; 
            border-collapse: collapse; 
            font-size: 13px; 
        }
        table.report th { 
            background: #f8fafc; 
            color: #475569; 
            padding: 14px 16px; 
            text-align: left; 
            font-weight: 600; 
            border-bottom: 1px solid #e2e8f0; 
        }
        table.report td { 
            padding: 14px 16px; 
            border-bottom: 1px solid #f1f5f9; 
            color: #1e293b; 
        }
        table.report tr:last-child td { border-bottom: none; }
        table.report tr.total td { 
            background: #f8fafc; 
            font-weight: 700; 
            color: #0f172a; 
            border-top: 1px solid #e2e8f0; 
        }

        /* UI Elements */
        .badge { 
            display: inline-block; 
            padding: 4px 10px; 
            border-radius: 6px; 
            font-size: 11px; 
            font-weight: 600; 
        }
        .badge-red { background: #fee2e2; color: #991b1b; }
        .badge-amber { background: #fef3c7; color: #92400e; }
        .badge-green { background: #dcfce7; color: #166534; }
        .badge-blue { background: #dbeafe; color: #1e40af; }

        .btn-container { text-align: center; margin-top: 32px; }
        .btn { 
            display: inline-block; 
            background: #2563eb; 
            color: #ffffff !important; 
            font-weight: 600; 
            text-decoration: none; 
            padding: 12px 28px; 
            border-radius: 8px; 
            font-size: 14px; 
            transition: all 0.2s; 
            box-shadow: 0 4px 6px -1px rgba(37, 99, 235, 0.2);
        }
        .btn-red { background: #dc2626; box-shadow: 0 4px 6px -1px rgba(220, 38, 38, 0.2); }

        .footer { 
            padding: 32px 48px; 
            background: #f8fafc; 
            text-align: center; 
            font-size: 12px; 
            color: #64748b; 
            border-top: 1px solid #e2e8f0; 
        }
        .footer p { margin: 4px 0; }
    </style>
    """


def get_payment_summary_html(report_data: dict, generated_at: str = None) -> str:
    """
    Generates Payment Summary (Order Tracking) report email.
    """
    if not generated_at:
        generated_at = datetime.now().strftime("%d %b %Y, %I:%M %p IST")

    owners = report_data.get("owners", [])
    grand_total = report_data.get("grand_total", {})

    rows_html = ""
    for row in owners:
        rows_html += f"""
        <tr>
            <td style="font-weight:500;">{row.get('owner_name', '-')}</td>
            <td>{_currency(row.get('activation_done_invoice_pending', 0))}</td>
            <td>{_currency(row.get('payment_pending', 0))}</td>
            <td>{_currency(row.get('po_received_activation_pending', 0))}</td>
            <td style="font-weight:700; color:#0f172a;">{_currency(row.get('grand_total', 0))}</td>
        </tr>
        """

    total_html = f"""
    <tr class="total">
        <td>Grand Total</td>
        <td>{_currency(grand_total.get('activation_done_invoice_pending', 0))}</td>
        <td>{_currency(grand_total.get('payment_pending', 0))}</td>
        <td>{_currency(grand_total.get('po_received_activation_pending', 0))}</td>
        <td style="color:#2563eb;">{_currency(grand_total.get('grand_total', 0))}</td>
    </tr>
    """

    return f"""
    <!DOCTYPE html>
    <html><head><meta charset="UTF-8"><title>Payment Summary Report</title>{_base_style()}</head>
    <body>
    <div class="container">
        <div class="header">
            <h1>📊 Payment Summary Report</h1>
            <p>Real-time snapshot of order statuses and outstanding receivables.</p>
        </div>
        <div class="body">
            <div class="stats-grid">
                <div class="stat-card">
                    <span class="label">Total Outstanding</span>
                    <span class="value">{_currency(grand_total.get('grand_total', 0))}</span>
                </div>
                <div class="stat-card">
                    <span class="label">Total Owners</span>
                    <span class="value">{len(owners)}</span>
                </div>
            </div>

            <div class="section-header">
                <h2 class="section-title">Owner Breakdown</h2>
                <div class="section-divider"></div>
            </div>

            <div class="table-container">
                <table class="report">
                    <thead><tr>
                        <th>Owner</th>
                        <th>Activation Done</th>
                        <th>Payment Pending</th>
                        <th>PO Received</th>
                        <th>Grand Total</th>
                    </tr></thead>
                    <tbody>
                        {rows_html}
                        {total_html}
                    </tbody>
                </table>
            </div>
            
            <div class="btn-container">
                <a href="{FRONTEND_URL}/report-view/payment_summary" class="btn">View in CRM Dashboard</a>
            </div>
        </div>
        <div class="footer">
            <p><strong>TIBOS CRM Intelligence</strong></p>
            <p>Generated on {generated_at}</p>
        </div>
    </div>
    </body></html>
    """


def get_payment_pending_html(report_data: dict, generated_at: str = None) -> str:
    """
    Generates Payment Pending report email.
    """
    if not generated_at:
        generated_at = datetime.now().strftime("%d %b %Y, %I:%M %p IST")

    owners = report_data.get("owners", [])
    grand_total = report_data.get("grand_total", {})
    owner_summaries = report_data.get("owner_summaries", [])

    summary_html = ""
    for s in owner_summaries:
        summary_html += f"""
        <tr>
            <td style="font-weight:500;">{s.get('owner_name', '-')}</td>
            <td><span class="badge badge-blue">{s.get('total_invoice_count', 0)} Invoices</span></td>
            <td>{_currency(s.get('total_invoice_amount', 0))}</td>
            <td style="color:#dc2626; font-weight:700;">{_currency(s.get('total_pending_amount', 0))}</td>
        </tr>
        """

    rows_html = ""
    for row in owners:
        rows_html += f"""
        <tr>
            <td style="font-weight:500;">{row.get('owner_name', '-')}</td>
            <td style="font-size:12px;">{row.get('customer_name', '-')}</td>
            <td style="color:#64748b; font-family:monospace;">{row.get('order_id', '-')}</td>
            <td>{row.get('invoice_count', 0)}</td>
            <td>{_currency(row.get('invoice_amount', 0))}</td>
            <td style="color:#dc2626; font-weight:600;">{_currency(row.get('pending_amount', 0))}</td>
        </tr>
        """

    total_html = f"""
    <tr class="total">
        <td colspan="3">Grand Total</td>
        <td>{grand_total.get('invoice_count', 0)}</td>
        <td>{_currency(grand_total.get('invoice_amount', 0))}</td>
        <td style="color:#dc2626;">{_currency(grand_total.get('pending_amount', 0))}</td>
    </tr>
    """

    return f"""
    <!DOCTYPE html>
    <html><head><meta charset="UTF-8"><title>Payment Pending Report</title>{_base_style()}</head>
    <body>
    <div class="container">
        <div class="header" style="background: linear-gradient(135deg, #7f1d1d 0%, #b91c1c 100%);">
            <h1>💰 Payment Pending Report</h1>
            <p>Immediate attention required for overdue invoices across all customers.</p>
        </div>
        <div class="body">
            <div class="stats-grid">
                <div class="stat-card">
                    <span class="label">Total Pending</span>
                    <span class="value" style="color:#dc2626;">{_currency(grand_total.get('pending_amount', 0))}</span>
                </div>
                <div class="stat-card">
                    <span class="label">Active Invoices</span>
                    <span class="value">{grand_total.get('invoice_count', 0)}</span>
                </div>
            </div>

            <div class="section-header">
                <h2 class="section-title">Owner Summary</h2>
                <div class="section-divider"></div>
            </div>
            <div class="table-container">
                <table class="report">
                    <thead><tr><th>Owner</th><th>Count</th><th>Total Amount</th><th>Pending</th></tr></thead>
                    <tbody>{summary_html}</tbody>
                </table>
            </div>

            <div class="section-header" style="margin-top:32px;">
                <h2 class="section-title">Detailed Breakdown</h2>
                <div class="section-divider"></div>
            </div>
            <div class="table-container">
                <table class="report">
                    <thead><tr>
                        <th>Owner</th><th>Customer</th><th>Order ID</th><th>Qty</th><th>Amount</th><th>Pending</th>
                    </tr></thead>
                    <tbody>
                        {rows_html}
                        {total_html}
                    </tbody>
                </table>
            </div>
            
            <div class="btn-container">
                <a href="{FRONTEND_URL}/report-view/payment_pending" class="btn btn-red">Take Action on Pending Payments</a>
            </div>
        </div>
        <div class="footer">
            <p><strong>TIBOS CRM Intelligence</strong></p>
            <p>Generated on {generated_at}</p>
        </div>
    </div>
    </body></html>
    """


def get_pending_invoice_alert_html(flagged_orders: list, days_threshold: int, generated_at: str = None) -> str:
    """
    Generates Pending Invoice Alert email.
    """
    if not generated_at:
        generated_at = datetime.now().strftime("%d %b %Y, %I:%M %p IST")

    rows_html = ""
    for order in flagged_orders:
        days = order.get("days_since_created", 0)
        badge_cls = "badge-red" if days > 30 else ("badge-amber" if days > 7 else "badge-blue")
        rows_html += f"""
        <tr>
            <td style="font-weight:600; font-family:monospace;">{order.get('order_id', '-')}</td>
            <td style="font-weight:500;">{order.get('customer_name', '-')}</td>
            <td>{order.get('owner_name', '-')}</td>
            <td style="color:#64748b;">{order.get('created_date', '-')}</td>
            <td><span class="badge {badge_cls}">{days} days</span></td>
            <td><span class="badge" style="background:#f1f5f9; color:#475569;">{order.get('invoice_status', '-')}</span></td>
        </tr>
        """

    return f"""
    <!DOCTYPE html>
    <html><head><meta charset="UTF-8"><title>Pending Invoice Alert</title>{_base_style()}</head>
    <body>
    <div class="container">
        <div class="header" style="background: linear-gradient(135deg, #92400e 0%, #d97706 100%);">
            <h1>📋 Pending Invoice Alert</h1>
            <p>Orders older than {days_threshold} day(s) with incomplete invoices requiring attention.</p>
        </div>
        <div class="body">
            <div style="background: #fffbeb; border: 1px solid #fef3c7; border-radius: 12px; padding: 20px; margin-bottom: 24px; color: #92400e; font-size: 14px;">
                <strong style="display:block; margin-bottom:4px;">⚠️ Attention Required</strong>
                {len(flagged_orders)} order(s) have been created more than <strong>{days_threshold} day(s)</strong> ago but invoices remain in "Incompleted" status.
            </div>

            <div class="stats-grid">
                <div class="stat-card">
                    <span class="label">Flagged Orders</span>
                    <span class="value" style="color:#d97706;">{len(flagged_orders)}</span>
                </div>
                <div class="stat-card">
                    <span class="label">Threshold</span>
                    <span class="value">{days_threshold} Days</span>
                </div>
            </div>

            <div class="table-container">
                <table class="report">
                    <thead><tr>
                        <th>Order ID</th><th>Customer</th><th>Owner</th><th>Created</th><th>Age</th><th>Status</th>
                    </tr></thead>
                    <tbody>{rows_html}</tbody>
                </table>
            </div>
            
            <div class="btn-container">
                <a href="{FRONTEND_URL}/orders" class="btn" style="background:#d97706;">Review Flagged Orders</a>
            </div>
        </div>
        <div class="footer">
            <p><strong>TIBOS CRM Intelligence</strong></p>
            <p>Generated on {generated_at}</p>
        </div>
    </div>
    </body></html>
    """


def get_activation_date_alert_html(upcoming_orders: list, overdue_orders: list, days_before: int, days_after: int, generated_at: str = None) -> str:
    """
    Generates Activation Date Alert email.
    """
    if not generated_at:
        generated_at = datetime.now().strftime("%d %b %Y, %I:%M %p IST")

    def _render_rows(orders, is_overdue=False):
        html = ""
        for order in orders:
            diff_label = "days past" if is_overdue else "days until"
            badge_cls = "badge-red" if is_overdue else "badge-blue"
            html += f"""
            <tr>
                <td style="font-weight:600; font-family:monospace;">{order.get('order_id', '-')}</td>
                <td style="font-weight:500;">{order.get('customer_name', '-')}</td>
                <td>{order.get('owner_name', '-')}</td>
                <td style="color:#64748b;">{order.get('activation_date', '-')}</td>
                <td><span class="badge {badge_cls}">{order.get('days_diff', 0)} {diff_label}</span></td>
            </tr>
            """
        return html

    upcoming_html = _render_rows(upcoming_orders) if upcoming_orders else '<tr><td colspan="5" style="text-align:center; padding:32px; color:#94a3b8; font-style:italic;">No upcoming activations found in this window.</td></tr>'
    overdue_html = _render_rows(overdue_orders, is_overdue=True) if overdue_orders else '<tr><td colspan="5" style="text-align:center; padding:32px; color:#94a3b8; font-style:italic;">Excellent! No overdue activations found.</td></tr>'

    return f"""
    <!DOCTYPE html>
    <html><head><meta charset="UTF-8"><title>Activation Date Alert</title>{_base_style()}</head>
    <body>
    <div class="container">
        <div class="header" style="background: linear-gradient(135deg, #065f46 0%, #059669 100%);">
            <h1>📅 Activation Date Alert</h1>
            <p>Monitoring orders approaching or past their scheduled delivery/activation dates.</p>
        </div>
        <div class="body">
            <div class="stats-grid">
                <div class="stat-card">
                    <span class="label">Upcoming</span>
                    <span class="value" style="color:#059669;">{len(upcoming_orders)}</span>
                </div>
                <div class="stat-card">
                    <span class="label">Overdue</span>
                    <span class="value" style="color:#dc2626;">{len(overdue_orders)}</span>
                </div>
            </div>

            <div class="section-header">
                <h2 class="section-title">🔜 Upcoming (Next {days_before} Days)</h2>
                <div class="section-divider"></div>
            </div>
            <div class="table-container">
                <table class="report">
                    <thead><tr><th>Order ID</th><th>Customer</th><th>Owner</th><th>Activation Date</th><th>Diff</th></tr></thead>
                    <tbody>{upcoming_html}</tbody>
                </table>
            </div>

            <div class="section-header" style="margin-top:32px;">
                <h2 class="section-title" style="color:#dc2626;">⚠️ Overdue (Past {days_after} Days)</h2>
                <div class="section-divider"></div>
            </div>
            <div class="table-container">
                <table class="report" style="border-top: 2px solid #fee2e2;">
                    <thead><tr><th>Order ID</th><th>Customer</th><th>Owner</th><th>Activation Date</th><th>Diff</th></tr></thead>
                    <tbody>{overdue_html}</tbody>
                </table>
            </div>
            
            <div class="btn-container">
                <a href="{FRONTEND_URL}/orders" class="btn" style="background:#059669;">Manage Deliveries</a>
            </div>
        </div>
        <div class="footer">
            <p><strong>TIBOS CRM Intelligence</strong></p>
            <p>Generated on {generated_at}</p>
        </div>
    </div>
    </body></html>
    """


def get_combined_report_html(
    payment_summary_data: dict,
    payment_pending_data: dict,
    cadence: str = "Daily",
    from_date_str: str = None,
    to_date_str: str = None,
    from_date_iso: str = None,
    to_date_iso: str = None,
    generated_at: str = None
) -> str:

    from datetime import datetime, timedelta

    if not generated_at:
        generated_at = datetime.now().strftime("%d %b %Y, %I:%M %p IST")

    # Fallback to current month if dates are not provided
    if not from_date_iso or not to_date_iso:
        today = datetime.now()
        if not from_date_iso:
            from_date_iso = today.replace(day=1).strftime("%Y-%m-%d")
        if not to_date_iso:
            to_date_iso = today.strftime("%Y-%m-%d")
            
    if not from_date_str:
        from_date_str = datetime.strptime(from_date_iso, "%Y-%m-%d").strftime("%d %b %Y")
    if not to_date_str:
        to_date_str = datetime.strptime(to_date_iso, "%Y-%m-%d").strftime("%d %b %Y")

    LOGO_URL = "https://tibosstaticassets.blob.core.windows.net/tibossiteassets/TIBOS_WEB/Logo/tibos%20logo.png"

    # Use the global FRONTEND_URL defined at the top of the file
    from templates.email.alert_report import FRONTEND_URL

    # =========================================================
    # PAYMENT SUMMARY
    # =========================================================

    owners = payment_summary_data.get("owners", [])
    gt_summary = payment_summary_data.get("grand_total", {})

    summary_rows = ""

    for row in owners:

        summary_rows += f"""
        <tr>

            <td class="owner">
                {row.get('owner_name', '-')}
            </td>

            <td>
                {_currency(row.get('activation_done_invoice_pending', 0))}
            </td>

            <td class="danger">
                {_currency(row.get('payment_pending', 0))}
            </td>

            <td>
                {_currency(row.get('po_received_activation_pending', 0))}
            </td>

            <td class="primary">
                {_currency(row.get('grand_total', 0))}
            </td>

        </tr>
        """

    summary_rows += f"""
    <tr class="total-row">

        <td>Total</td>

        <td>
            {_currency(gt_summary.get('activation_done_invoice_pending', 0))}
        </td>

        <td class="danger">
            {_currency(gt_summary.get('payment_pending', 0))}
        </td>

        <td>
            {_currency(gt_summary.get('po_received_activation_pending', 0))}
        </td>

        <td class="primary">
            {_currency(gt_summary.get('grand_total', 0))}
        </td>

    </tr>
    """

    # =========================================================
    # PAYMENT PENDING
    # =========================================================

    pending_summaries = payment_pending_data.get("owner_summaries", [])
    gt_pending = payment_pending_data.get("grand_total", {})

    pending_summary_rows = ""

    for row in pending_summaries:

        pending_summary_rows += f"""
        <tr>

            <td class="owner">
                {row.get('owner_name', '-')}
            </td>

            <td>

                <span class="invoice-badge">
                    {row.get('total_invoice_count', 0)} Invoices
                </span>

            </td>

            <td>
                {_currency(row.get('total_invoice_amount', 0))}
            </td>

            <td class="danger">
                {_currency(row.get('total_pending_amount', 0))}
            </td>

        </tr>
        """

    return f"""
<!DOCTYPE html>

<html lang="en">

<head>

    <meta charset="UTF-8">

    <meta
        name="viewport"
        content="width=device-width, initial-scale=1.0"
    >

    <title>{cadence} Payment Report</title>

    <style>
    :root {{

    --bg-primary: #ffffff;
    --bg-secondary: #f8fafc;

    --border-color: #e2e8f0;

    --text-primary: #0f172a;
    --text-secondary: #475569;

    --btn-blue-start: #2563eb;
    --btn-blue-end: #1d4ed8;

    --btn-red-start: #ef4444;
    --btn-red-end: #dc2626;

    --shadow-blue: rgba(37,99,235,0.25);
    --shadow-red: rgba(239,68,68,0.25);
}}

        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        @media (prefers-color-scheme: dark) {{

    :root {{

        --bg-primary: #0f172a;
        --bg-secondary: #1e293b;

        --border-color: #334155;

        --text-primary: #f8fafc;
        --text-secondary: #cbd5e1;

        --btn-blue-start: #3b82f6;
        --btn-blue-end: #2563eb;

        --btn-red-start: #f87171;
        --btn-red-end: #ef4444;

        --shadow-blue: rgba(59,130,246,0.35);
        --shadow-red: rgba(248,113,113,0.35);
    }}
}}

        body {{
            background: #eef2f7;
            font-family: Arial, Helvetica, sans-serif;
            padding: 30px 15px;
            color: #1e293b;
        }}

        .main-container {{
            max-width: 1100px;
            margin: auto;
            background: #ffffff;
            border-radius: 22px;
            overflow: hidden;
            box-shadow: 0 10px 35px rgba(0,0,0,0.08);
        }}

        /* ===================================================== */
        /* HEADER */
        /* ===================================================== */

        .header {{
            background: #ffffff;
            padding: 55px 40px 40px;
            text-align: center;
        }}

        .logo {{
            width: 340px;
            max-width: 100%;
            object-fit: contain;
            margin-bottom: 22px;
        }}

        .title {{
            font-size: 42px;
            font-weight: 700;
            color: #0f172a;
            margin-bottom: 34px;
            line-height: 1.2;
        }}

        /* ===================================================== */
        /* DATE CARD */
        /* ===================================================== */

        .date-card {{
            width: fit-content;
            margin: auto;
            background: #f8fbff;
            border: 1px solid #dbe7f3;
            border-radius: 18px;
            padding: 24px 60px;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 100px;
            margin-top: 10px;
        }}

        .date-block {{
            min-width: 180px;
            text-align: center;
        }}

        .date-label {{
            font-size: 13px;
            color: #64748b;
            margin-bottom: 10px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}

        .date-value {{
            font-size: 26px;
            font-weight: 700;
            color: #2563eb;
            white-space: nowrap;
        }}

        .divider {{
            width: 1px;
            height: 60px;
            background: #dbe7f3;
        }}

        /* ===================================================== */
        /* CONTENT */
        /* ===================================================== */

        .content {{
            padding: 20px 40px 40px;
        }}

        /* ===================================================== */
        /* KPI GRID */
        /* ===================================================== */

        .kpi-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 28px;
            margin-top: 35px;
            margin-bottom: 50px;
        }}

        .kpi-card {{
            border-radius: 22px;
            padding: 30px;
            display: flex;
            align-items: center;
            gap: 22px;
            border: 1px solid #e2e8f0;
            background: #ffffff;
        }}

        .kpi-icon {{
            width: 78px;
            height: 78px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 34px;
            color: white;
            flex-shrink: 0;
        }}

        .blue-bg {{
            background: linear-gradient(135deg, #2563eb, #1d4ed8);
        }}

        .red-bg {{
            background: linear-gradient(135deg, #ef4444, #dc2626);
        }}

        .kpi-label {{
            font-size: 15px;
            color: #475569;
            margin-bottom: 10px;
            font-weight: 600;
        }}

        .kpi-value {{
            font-size: 44px;
            font-weight: 700;
            line-height: 1;
        }}

        .blue-text {{
            color: #2563eb;
        }}

        .red-text {{
            color: #ef4444;
        }}

        /* ===================================================== */
        /* SECTION */
        /* ===================================================== */

        .section {{
            margin-top: 40px;
        }}

        .section-header {{
            display: flex;
            align-items: center;
            gap: 14px;
            margin-bottom: 18px;
        }}

        .section-icon {{
            font-size: 26px;
        }}

        .section-title {{
            font-size: 30px;
            font-weight: 700;
            color: #0f172a;
            white-space: nowrap;
        }}

        .section-line {{
            height: 1px;
            flex: 1;
            background: #e2e8f0;
        }}

        /* ===================================================== */
        /* TABLE */
        /* ===================================================== */

        .table-wrapper {{
            border: 1px solid #e2e8f0;
            border-radius: 18px;
            overflow: hidden;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
        }}

        thead {{
            background: #f8fafc;
        }}

        th {{
            padding: 20px;
            text-align: left;
            font-size: 13px;
            text-transform: uppercase;
            color: #475569;
            border-bottom: 1px solid #e2e8f0;
        }}

        td {{
            padding: 20px;
            border-bottom: 1px solid #f1f5f9;
            font-size: 15px;
        }}

        .owner {{
            font-weight: 700;
        }}

        .danger {{
            color: #ef4444;
            font-weight: 700;
        }}

        .primary {{
            color: #2563eb;
            font-weight: 700;
        }}

        .total-row {{
            background: #eff6ff;
            font-weight: 700;
        }}

        .invoice-badge {{
            display: inline-block;
            background: #dbeafe;
            color: #2563eb;
            padding: 8px 14px;
            border-radius: 999px;
            font-size: 12px;
            font-weight: 700;
        }}

.btn-row {{
    margin-top: 30px;
    background-color: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 18px;
    padding: 24px;
    text-align: center;
}}

.btn {{
    display: inline-block;
    padding: 15px 32px;
    border-radius: 12px;
    text-decoration: none;
    font-size: 14px;
    font-weight: 700;
    margin: 8px;
}}

.btn-blue {{
    background-color: #2563eb;
    color: #ffffff !important;
}}

.btn-red {{
    background-color: #ef4444;
    color: #ffffff !important;
}}

/* ===================================================== */
/* HOVER */
/* ===================================================== */

.btn:hover {{

    transform: translateY(-2px);
    opacity: 0.96;
}}

        /* ===================================================== */
        /* FOOTER */
        /* ===================================================== */

        .footer {{
            margin-top: 50px;
            background: linear-gradient(135deg, #020617, #0f172a);
            padding: 35px;
            text-align: center;
            color: rgba(255,255,255,0.85);
        }}

        .footer-title {{
            color: white;
            font-size: 20px;
            font-weight: 700;
            margin-bottom: 10px;
        }}

        .footer-text {{
            font-size: 14px;
            margin-top: 6px;
        }}

        /* ===================================================== */
        /* MOBILE */
        /* ===================================================== */

        @media(max-width: 768px) {{

            .title {{
                font-size: 30px;
            }}

            .logo {{
                width: 240px;
            }}

            .date-card {{
                width: 100%;
                flex-direction: column;
                gap: 24px;
            }}

            .divider {{
                width: 100%;
                height: 1px;
            }}

            .kpi-grid {{
                grid-template-columns: 1fr;
            }}

            .kpi-card {{
                flex-direction: column;
                text-align: center;
            }}

            .btn-row {{
                flex-direction: column;
            }}

            .btn {{
                width: 100%;
            }}

            .content {{
                padding: 20px;
            }}
        }}

    </style>

</head>

<body>

<div class="main-container">

    <!-- ===================================================== -->
    <!-- HEADER -->
    <!-- ===================================================== -->

    <div class="header">

        <img
            src="{LOGO_URL}"
            class="logo"
            alt="TIBOS Logo"
        >

        <div class="title">
            {cadence} — Payment Summary & Pending Report
        </div>

        <div class="date-card">

            <div class="date-block">

                <div class="date-label">
                    From
                </div>

                <div class="date-value">
                    {from_date_str or "-"}
                </div>

            </div>

            <div class="divider"></div>

            <div class="date-block">

                <div class="date-label">
                    To
                </div>

                <div class="date-value">
                    {to_date_str or "-"}
                </div>

            </div>

        </div>

    </div>

    <!-- ===================================================== -->
    <!-- CONTENT -->
    <!-- ===================================================== -->

    <div class="content">

        <!-- KPI -->

        <div class="kpi-grid">

            <div class="kpi-card">

                <div class="kpi-icon blue-bg">
                    💳
                </div>

                <div>

                    <div class="kpi-label">
                        Total Outstanding
                    </div>

                    <div class="kpi-value blue-text">
                        {_currency(gt_summary.get('grand_total', 0))}
                    </div>

                </div>

            </div>

            <div class="kpi-card">

                <div class="kpi-icon red-bg">
                    📄
                </div>

                <div>

                    <div class="kpi-label">
                        Payment Pending
                    </div>

                    <div class="kpi-value red-text">
                        {_currency(gt_pending.get('pending_amount', 0))}
                    </div>

                </div>

            </div>

        </div>

        <!-- PAYMENT SUMMARY -->

        <div class="section">

            <div class="section-header">

                <div class="section-icon">
                    📊
                </div>

                <div class="section-title">
                    Payment Summary
                </div>

                <div class="section-line"></div>

            </div>

            <div class="table-wrapper">

                <table>

                    <thead>

                        <tr>
                            <th>Owner</th>
                            <th>Activation Done</th>
                            <th>Payment Pending</th>
                            <th>PO Received</th>
                            <th>Total</th>
                        </tr>

                    </thead>

                    <tbody>

                        {summary_rows}

                    </tbody>

                </table>

            </div>

        </div>

        <!-- PAYMENT PENDING -->

        <div class="section">

            <div class="section-header">

                <div class="section-icon">
                    💰
                </div>

                <div class="section-title">
                    Pending Collections
                </div>

                <div class="section-line"></div>

            </div>

            <div class="table-wrapper">

                <table>

                    <thead>

                        <tr>
                            <th>Owner</th>
                            <th>Invoices</th>
                            <th>Invoice Amount</th>
                            <th>Pending Amount</th>
                        </tr>

                    </thead>

                    <tbody>

                        {pending_summary_rows}

                    </tbody>

                </table>

            </div>

        </div>

        <!-- BUTTONS -->

        <div class="btn-row">

            <a
                href="{FRONTEND_URL}/report-view/payment_summary?from_date={from_date_iso}&to_date={to_date_iso}&date_by=ACTIVATION_DATE"
                class="btn btn-blue"
                target="_blank"
            >
                View Payment Summary
            </a>

            <a
                href="{FRONTEND_URL}/report-view/payment_pending?from_date={from_date_iso}&to_date={to_date_iso}&min_days_pending=0&date_by=ACTIVATION_DATE"
                class="btn btn-red"
                target="_blank"
            >
                View Payment Pending
            </a>

        </div>

    </div>

    <!-- FOOTER -->

    <div class="footer">

        <div class="footer-title">
            TIBOS CRM Intelligence
        </div>

        <div class="footer-text">
            Generated on {generated_at}
        </div>

        <div class="footer-text">
            This is an automated report generated by the TIBOS CRM system.
        </div>

    </div>

</div>

</body>

</html>
"""