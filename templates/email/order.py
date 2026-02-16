def get_crm_order_email_content(
    customer_name: str,
    order_id: str,
    company_name: str,
    items: list,
    total_amount: float,
    currency: str = "₹",
    support_email: str = "support@tibos.in",
    footer_note: str = "Thank you for choosing us.",
) -> str:
    """
    Returns a professional HTML order confirmation email
    """

    # Build table rows
    rows_html = ""
    for item in items:
        line_total = item["qty"] * item["price"]
        rows_html += f"""
        <tr>
            <td style="padding:8px;border:1px solid #e5e7eb;">{item["name"]}</td>
            <td style="padding:8px;border:1px solid #e5e7eb;text-align:center;">{item["qty"]}</td>
            <td style="padding:8px;border:1px solid #e5e7eb;text-align:right;">
                {currency}{item["price"]:,.2f}
            </td>
            <td style="padding:8px;border:1px solid #e5e7eb;text-align:right;">
                {currency}{line_total:,.2f}
            </td>
        </tr>
        """

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8" />
        <title>Order Confirmation</title>
    </head>
    <body style="font-family:Arial,Helvetica,sans-serif;background:#f9fafb;padding:20px;">
        <table width="100%" cellspacing="0" cellpadding="0">
            <tr>
                <td align="center">
                    <table width="600" cellpadding="0" cellspacing="0"
                        style="background:#ffffff;border-radius:8px;padding:24px;box-shadow:0 4px 12px rgba(0,0,0,0.05);">
                        
                        <!-- HEADER -->
                        <tr>
                            <td style="text-align:center;padding-bottom:20px;">
                                <h2 style="margin:0;color:#111827;">{company_name}</h2>
                                <p style="margin:4px 0;color:#6b7280;font-size:14px;">
                                    Order Confirmation
                                </p>
                            </td>
                        </tr>

                        <!-- GREETING -->
                        <tr>
                            <td style="padding-bottom:16px;color:#111827;">
                                Hi <strong>{customer_name}</strong>,
                                <br/><br/>
                                Thank you for your order. Below are the details of your purchase.
                            </td>
                        </tr>

                        <!-- ORDER INFO -->
                        <tr>
                            <td style="padding-bottom:16px;">
                                <strong>Order ID:</strong> {order_id}
                            </td>
                        </tr>

                        <!-- ITEMS TABLE -->
                        <tr>
                            <td>
                                <table width="100%" cellpadding="0" cellspacing="0"
                                    style="border-collapse:collapse;font-size:14px;">
                                    <thead>
                                        <tr style="background:#f3f4f6;">
                                            <th style="padding:8px;border:1px solid #e5e7eb;text-align:left;">Item</th>
                                            <th style="padding:8px;border:1px solid #e5e7eb;text-align:center;">Qty</th>
                                            <th style="padding:8px;border:1px solid #e5e7eb;text-align:right;">Price</th>
                                            <th style="padding:8px;border:1px solid #e5e7eb;text-align:right;">Total</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {rows_html}
                                    </tbody>
                                </table>
                            </td>
                        </tr>

                        <!-- TOTAL -->
                        <tr>
                            <td style="padding-top:16px;text-align:right;font-size:16px;">
                                <strong>Grand Total: {currency}{total_amount:,.2f}</strong>
                            </td>
                        </tr>

                        <!-- FOOTER -->
                        <tr>
                            <td style="padding-top:24px;color:#374151;font-size:14px;">
                                {footer_note}
                                <br/><br/>
                                If you have any questions, contact us at
                                <a href="mailto:{support_email}" style="color:#2563eb;">
                                    {support_email}
                                </a>
                            </td>
                        </tr>

                        <tr>
                            <td style="padding-top:16px;color:#9ca3af;font-size:12px;text-align:center;">
                                © {company_name}. All rights reserved.
                            </td>
                        </tr>

                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """

    return html
