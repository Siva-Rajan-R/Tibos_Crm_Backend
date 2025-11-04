from pydantic import EmailStr
from data_formats.enums.common_enums import UserRoles

def get_user_accept_email_content(user_name:str,user_email:EmailStr,user_role:UserRoles,accept_link:str,profile_pic_link:str) -> str:
    return f"""
<!DOCTYPE html>
<html>
  <head>
    <meta charset="UTF-8" />
    <title>Accepted</title>
  </head>

  <body style="margin:0; padding:0; background:#f6f7f9;">
    <table width="100%" cellpadding="0" cellspacing="0" style="background:#f6f7f9; padding:20px 0;">
      <tr>
        <td align="center">
          
          <!-- CARD -->
          <table width="450" cellpadding="0" cellspacing="0" style="background:#ffffff; border-radius:12px; padding:30px; border:1px solid #e5e7eb; font-family:Arial, sans-serif;">
            
            <!-- Heading -->
            <tr>
              <td align="center" style="padding-bottom:20px;">
                <h2 style="margin:0; font-size:24px; color:#1e293b; font-weight:700;">
                  Registeration Accept
                </h2>
                <p style="margin:5px 0 0; font-size:13px; color:#64748b;">
                  { user_name } — Requested to use the Tibos CRM.
                </p>
              </td>
            </tr>

            <!-- Green Check Circle -->
            <tr>
              <td align="center" style="padding-bottom:20px;">
                <img 
                  src="{ profile_pic_link }"
                  alt="Profile Picture"
                  width="60"
                  height="60"
                  style="
                    border-radius:50%;
                    display:block;
                    object-fit:cover;
                  "
                />
              </td>
            </tr>

            <!-- Name -->
            <tr>
              <td style="padding:12px; background:#f8fafc; border-radius:8px; margin-bottom:6px;">
                <strong style="font-size:12px; color:#64748b;">Name</strong><br />
                <span style="font-size:14px; color:#1e293b; font-weight:bold;">
                  {user_name}
                </span>
              </td>
            </tr>

            <!-- Email -->
            <tr>
              <td style="padding:12px; background:#f8fafc; border-radius:8px; margin-bottom:6px;">
                <strong style="font-size:12px; color:#64748b;">Email</strong><br />
                <span style="font-size:14px; color:#1e293b; font-weight:bold;">
                  {user_email}
                </span>
              </td>
            </tr>

            <!-- Role -->
            <tr>
              <td style="padding:12px; background:#f8fafc; border-radius:8px;">
                <strong style="font-size:12px; color:#64748b;">Role</strong><br />
                <span style="font-size:14px; color:#1e293b; font-weight:bold;">
                  {user_role}
                </span>
              </td>
            </tr>

            <!-- Buttons -->
            <tr>
              <td align="right" style="padding-top:20px;">
                <a href="{accept_link}"
                  style="padding:10px 16px; font-size:14px; border:1px solid #059669; color:#059669; text-decoration:none; border-radius:6px; margin-right:8px; display:inline-block;">
                  Accept
                </a>
              </td>
            </tr>
            <strong style="font-size:12px; color:#64748b;">If it looks supicious, Just leave it.</strong>
          </table>
          <!-- END CARD -->

        </td>
      </tr>
    </table>
  </body>
</html>

    """