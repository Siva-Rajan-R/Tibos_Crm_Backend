from pydantic import EmailStr
from core.data_formats.enums.user_enums import UserRoles

def get_accepted_email_content(user_name:str,user_email:EmailStr,user_role:UserRoles,dashboard_link:str,profile_pic_link:str) -> str:
    return f"""<!DOCTYPE html>
<html>
  <head>
    <meta charset="UTF-8" />
    <title>Registration Accepted</title>
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
                  Registration Accepted
                </h2>
                <p style="margin:6px 0 20px; font-size:13px; color:#64748b;">
                  Your account has been successfully approved. Now you can access the Tibos CRM platform.
                </p>
              </td>
            </tr>

            <!-- Profile Picture / Letter -->
            <tr>
              <td align="center" style="padding-bottom:20px;">
                <img src="{ profile_pic_link }"
                     alt="Profile Picture"
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

            <!-- Role -->
            <tr>
              <td style="padding:12px; background:#f8fafc; border-radius:10px;">
                <div style="font-size:11px; color:#64748b;">Role</div>
                <div style="font-size:15px; font-weight:bold; color:#1e293b;">
                  { user_role }
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

            <tr>
              <td align="center" style="padding-top:25px;">
                <p style="font-size:11px; color:#94a3b8;">
                  Thank you for joining our platform.
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



def get_login_credential_email_content(user_name: str, user_email: EmailStr, user_role:UserRoles, password: str, dashboard_link: str) -> str:
    return f"""<!DOCTYPE html>
<html>
  <head>
    <meta charset="UTF-8" />
    <title>Login Credentials</title>
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
                  Login Credentials
                </h2>
                <p style="margin:6px 0 20px; font-size:13px; color:#64748b;">
                  Your account has been created successfully. Use the credentials below to access the platform.
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

            <!-- Password -->
            <tr>
              <td style="padding:12px; background:#f8fafc; border-radius:10px;">
                <div style="font-size:11px; color:#64748b;">Password</div>
                <div style="font-size:15px; font-weight:bold; color:#1e293b;">
                  { password }
                </div>
              </td>
            </tr>

            <!-- Role -->
            <tr>
              <td style="padding:12px; background:#f8fafc; border-radius:10px; margin-bottom:8px;">
                <div style="font-size:11px; color:#64748b;">Role</div>
                <div style="font-size:15px; font-weight:bold; color:#1e293b;">
                  { user_role }
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

            <tr>
              <td align="center" style="padding-top:25px;">
                <p style="font-size:11px; color:#94a3b8;">
                  Please keep your login details confidential.
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
