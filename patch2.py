with open('api/routes/order.py', 'r') as f:
    content = f.read()

import re
# Remove the faulty route at the end of the file
content = re.sub(r'@router\.post\("/report/owner-sales"\)[\s\S]*', '', content)

new_route = '''
@router.post("/report/owner-sales")
async def get_owner_sales_report(data: OwnerSalesReportSchema, user:dict=Depends(verify_user), session:AsyncSession=Depends(get_pg_db_session)):
    return await HandleOrdersRequest(session=session, user_role=user['role'], cur_user_id=user['id']).get_owner_sales_report(data=data)
'''

with open('api/routes/order.py', 'w') as f:
    f.write(content + new_route + '\n')

# And in api/handlers/order_handler.py, the class is HandleOrdersRequest
# The function was already appended inside HandleOrdersRequest at the end, so no need to change handler unless indentation is wrong.
print("Done")
