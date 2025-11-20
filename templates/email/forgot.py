from pydantic import EmailStr

def get_forgot_password_email_content(user_name: str, user_email: EmailStr, reset_link: str) -> str:
    return f"""<!DOCTYPE html>
<html>
  <head>
    <meta charset="UTF-8" />
    <title>Reset Your Password</title>
  </head>

  <body style="margin:0; padding:0; background:#f6f7f9;">
    
    <table width="100%" cellpadding="0" cellspacing="0" style="padding:20px 0; background:#f6f7f9;">
      <tr>
        <td align="center">

          <table width="460" cellpadding="0" cellspacing="0" 
                 style="background:#ffffff; border-radius:14px; 
                        border:1px solid #e5e7eb; 
                        padding:30px; font-family:Arial, sans-serif;">

            <!-- Heading -->
            <tr>
              <td align="center">
                <h2 style="margin:0; font-size:24px; font-weight:bold; color:#1e293b;">
                  Reset Your Password
                </h2>
                <p style="margin:6px 0 20px; font-size:13px; color:#64748b;">
                  A request was made to reset your password. Click the button below to create a new one.
                </p>
              </td>
            </tr>

            <!-- Profile -->
            <tr>
              <td align="center" style="padding-bottom:20px;">
                <img src="https://ui-avatars.com/api/?name={user_name}&bold=true&background=random"
                     alt={user_name}
                     width="70" height="70"
                     style="border-radius:50%; display:block; object-fit:cover; box-shadow:0 3px 8px rgba(0,0,0,0.12);" />
              </td>
            </tr>

            <!-- Name -->
            <tr>
              <td style="padding:12px; background:#f8fafc; border-radius:10px; margin-bottom:8px;">
                <div style="font-size:11px; color:#64748b;">Name</div>
                <div style="font-size:15px; font-weight:bold; color:#1e293b;">
                  { user_name }
                </div>
              </td>
            </tr>

            <!-- Email -->
            <tr>
              <td style="padding:12px; background:#f8fafc; border-radius:10px; margin-bottom:8px;">
                <div style="font-size:11px; color:#64748b;">Email</div>
                <div style="font-size:15px; font-weight:bold; color:#1e293b;">
                  { user_email }
                </div>
              </td>
            </tr>

            <!-- Button -->
            <tr>
              <td align="center" style="padding-top:25px;">
                <a href="{ reset_link }"
                   style="
                     background:#059669; 
                     color:white; 
                     padding:12px 26px; 
                     border-radius:8px; 
                     text-decoration:none; 
                     font-size:14px; 
                     font-weight:bold;
                     display:inline-block;
                   ">
                  Reset Password
                </a>
              </td>
            </tr>

            <!-- Security Notice -->
            <tr>
              <td align="center" style="padding-top:25px;">
                <p style="font-size:11px; color:#94a3b8;">
                  If you did not request this, you can safely ignore the email.<br/>
                  This link will expire in 10 minutes.
                </p>
              </td>
            </tr>

          </table>

        </td>
      </tr>
    </table>

  </body>
</html>
"""


def get_password_reset_success_email(user_name: str, user_email: EmailStr, dashboard_link: str) -> str:
    return f"""<!DOCTYPE html>
<html>
  <head>
    <meta charset="UTF-8" />
    <title>Password Reset Successful</title>
  </head>

  <body style="margin:0; padding:0; background:#f6f7f9; font-family:Arial, sans-serif;">
    
    <table width="100%" cellpadding="0" cellspacing="0" style="padding:20px 0; background:#f6f7f9;">
      <tr>
        <td align="center">

          <table width="460" cellpadding="0" cellspacing="0" 
                 style="background:#ffffff; border-radius:14px; 
                        border:1px solid #e5e7eb; 
                        padding:30px;">

            <!-- Heading -->
            <tr>
              <td align="center">
                <h2 style="margin:0; font-size:24px; font-weight:bold; color:#1e293b;">
                  Password Updated
                </h2>
                <p style="margin:6px 0 20px; font-size:13px; color:#64748b;">
                  Your password has been changed successfully.
                </p>
              </td>
            </tr>

            <!-- Profile -->
            <tr>
              <td align="center" style="padding-bottom:20px;">
                <img src="https://ui-avatars.com/api/?name={user_name}&bold=true&background=random"
                     alt={user_name}
                     width="70" height="70"
                     style="border-radius:50%; display:block; object-fit:cover; box-shadow:0 3px 8px rgba(0,0,0,0.12);" />
              </td>
            </tr>

            <!-- Name -->
            <tr>
              <td style="padding:12px; background:#f8fafc; border-radius:10px; margin-bottom:8px;">
                <div style="font-size:11px; color:#64748b;">Name</div>
                <div style="font-size:15px; font-weight:bold; color:#1e293b;">
                  { user_name }
                </div>
              </td>
            </tr>

            <!-- Email -->
            <tr>
              <td style="padding:12px; background:#f8fafc; border-radius:10px;">
                <div style="font-size:11px; color:#64748b;">Email</div>
                <div style="font-size:15px; font-weight:bold; color:#1e293b;">
                  { user_email }
                </div>
              </td>
            </tr>

            <!-- Button -->
            <tr>
              <td align="center" style="padding-top:25px;">
                <a href="{ dashboard_link }"
                   style="
                     background:#059669;
                     color:white;
                     padding:12px 26px;
                     border-radius:8px;
                     text-decoration:none;
                     font-size:14px;
                     font-weight:bold;
                     display:inline-block;
                   ">
                  Go to Dashboard
                </a>
              </td>
            </tr>

            <!-- Footer note -->
            <tr>
              <td align="center" style="padding-top:25px;">
                <p style="font-size:11px; color:#94a3b8;">
                  If you did not perform this action, please reset your password immediately.
                </p>
              </td>
            </tr>

          </table>

        </td>
      </tr>
    </table>

  </body>
</html>
"""

