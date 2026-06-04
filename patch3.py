import re

with open('infras/primary_db/repos/order_repo.py', 'r') as f:
    content = f.read()

# The method starts with "    async def get_owner_sales_report(self, from_date, to_date, date_by, cur_user_id, user_role):"
# and goes to the end of the file.
method_match = re.search(r'    async def get_owner_sales_report\(self, from_date, to_date, date_by, cur_user_id, user_role\):.*', content, flags=re.DOTALL)

if method_match:
    method_code = method_match.group(0)
    # Remove it from the end of the file
    content = content.replace(method_code, '')
    
    # Insert it under class OrdersRepo(BaseRepoModel):
    # We will find "class OrdersRepo(BaseRepoModel):" and insert the method inside it.
    # To be safe, we'll insert it right before "class OrderTrackingReportRepo(OrdersRepo):"
    
    insert_pos = content.find('class OrderTrackingReportRepo(OrdersRepo):')
    if insert_pos != -1:
        new_content = content[:insert_pos] + method_code + '\n\n' + content[insert_pos:]
        
        with open('infras/primary_db/repos/order_repo.py', 'w') as f:
            f.write(new_content)
        print("Successfully moved method to OrdersRepo")
    else:
        print("Could not find insertion point")
else:
    print("Could not find method code")

