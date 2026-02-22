from pydantic import EmailStr


def get_report_download_email_content(
    user_email: EmailStr,
    report_name: str,
    record_count: int,
    download_link: str,
    expiry_hours: int = 24,
    footer_image_url: str | None = None,
) -> str:
    return f"""
<!DOCTYPE html>
<html>
  <head>
    <meta charset="UTF-8" />
    <title>Report Ready</title>
  </head>

  <body style="margin:0; padding:0; background:#f6f7f9;">
    <table width="100%" cellpadding="0" cellspacing="0" style="background:#f6f7f9; padding:24px 0;">
      <tr>
        <td align="center">

          <!-- CARD -->
          <table width="500" cellpadding="0" cellspacing="0"
            style="
              background:#ffffff;
              border-radius:14px;
              padding:32px;
              border:1px solid #e5e7eb;
              font-family:Arial, sans-serif;
            ">

            <!-- Header -->
            <tr>
              <td align="center" style="padding-bottom:22px;">
                <h2 style="margin:0; font-size:26px; color:#0f172a; font-weight:700;">
                  Your Report Is Ready
                </h2>
                <p style="margin:8px 0 0; font-size:13px; color:#64748b;">
                  Generated for <strong>{user_email}</strong>
                </p>
              </td>
            </tr>

            <!-- Report Details -->
            <tr>
              <td style="padding:14px; background:#f8fafc; border-radius:10px;">
                <strong style="font-size:12px; color:#64748b;">Report Name</strong><br />
                <span style="font-size:15px; color:#0f172a; font-weight:600;">
                  {report_name}
                </span>
              </td>
            </tr>

            <tr>
              <td style="padding:14px; background:#f8fafc; border-radius:10px; margin-top:8px;">
                <strong style="font-size:12px; color:#64748b;">Total Records</strong><br />
                <span style="font-size:15px; color:#0f172a; font-weight:600;">
                  {record_count}
                </span>
              </td>
            </tr>

            <!-- Alert Box -->
            <tr>
              <td style="padding-top:18px;">
                <table width="100%" cellpadding="0" cellspacing="0"
                  style="
                    background:#fef3c7;
                    border:1px solid #fde68a;
                    border-radius:10px;
                    padding:14px;
                  ">
                  <tr>
                    <td style="font-size:12px; color:#92400e; line-height:1.4;">
                      <strong>⚠️ Download Expiry Notice</strong><br />
                      This download link will expire in <strong>{expiry_hours} hours</strong>.
                      After expiry, you’ll need to request the report again.
                    </td>
                  </tr>
                </table>
              </td>
            </tr>

            <!-- Button -->
            <tr>
              <td align="center" style="padding-top:26px;">
                <a href="{download_link}"
                  style="
                    width:100%;
                    display:block;
                    text-align:center;
                    padding:14px 0;
                    font-size:15px;
                    background:#2563eb;
                    color:#ffffff;
                    text-decoration:none;
                    border-radius:10px;
                    font-weight:600;
                  ">
                  Download Report
                </a>
              </td>
            </tr>

            <!-- Footer Image -->
            {
                f'''
                <tr>
                  <td align="center" style="padding-top:28px;">
                    <img
                      src="{footer_image_url}"
                      alt="Footer Image"
                      width="180"
                      style="
                        display:block;
                        max-width:100%;
                        height:auto;
                        border-radius:8px;
                      "
                    />
                  </td>
                </tr>
                ''' if footer_image_url else ""
            }

            <!-- Footer Text -->
            <tr>
              <td style="padding-top:16px;">
                <p style="font-size:11px; color:#64748b; margin:0; text-align:center;">
                  If you did not request this report, you can safely ignore this email.
                </p>
              </td>
            </tr>

          </table>
          <!-- END CARD -->

        </td>
      </tr>
    </table>
  </body>
</html>
"""