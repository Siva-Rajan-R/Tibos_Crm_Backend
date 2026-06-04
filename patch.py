import os

# 1. order_repo.py
repo_code = '''
    async def get_owner_sales_report(self, from_date, to_date, date_by, cur_user_id, user_role):
        conditions = []
        if from_date:
            from_dt = datetime.combine(from_date, datetime.min.time())
            if date_by.value == "ACTIVATION_DATE":
                conditions.append(Orders.activation_date >= from_dt)
            elif date_by.value == "ORDER_DATE":
                conditions.append(Orders.order_date >= from_dt)
            else:
                conditions.append(Orders.created_at >= from_dt)
        if to_date:
            to_dt = datetime.combine(to_date, datetime.max.time())
            if date_by.value == "ACTIVATION_DATE":
                conditions.append(Orders.activation_date <= to_dt)
            elif date_by.value == "ORDER_DATE":
                conditions.append(Orders.order_date <= to_dt)
            else:
                conditions.append(Orders.created_at <= to_dt)
        
        if user_role == UserRoles.USER.value:
            conditions.append(Orders.owner_id == cur_user_id)
            
        owner_label = func.coalesce(Users.name, "Unknown").label("owner_name")
        product_type = Orders.logistic_info["product_type"].astext.label("product_type")
        
        stmt = (
            select(
                owner_label,
                Orders.customer_price.label("customer_price"),
                Orders.total_price.label("total_price"),
                Orders.logistic_info["purchase_type"].astext.label("purchase_type"),
                product_type
            )
            .select_from(Orders)
            .join(Users, Users.id == Orders.owner_id, isouter=True)
            .where(*conditions)
        )
        
        result = await self.session.execute(stmt)
        rows = result.all()
        
        owner_map = {}
        for row in rows:
            o_name = row.owner_name
            c_price = float(row.customer_price or 0)
            t_price = float(row.total_price or 0)
            val = t_price if t_price else c_price
            p_type = row.product_type
            purchase_type = row.purchase_type
            
            if o_name not in owner_map:
                owner_map[o_name] = {
                    "owner_name": o_name,
                    "total_order_value": 0,
                    "net_new_customer_value": 0,
                    "product_types": {}
                }
            
            owner_map[o_name]["total_order_value"] += val
            
            if purchase_type == "NET-NEW-CUSTOMER":
                owner_map[o_name]["net_new_customer_value"] += val
                
            if p_type:
                if p_type not in owner_map[o_name]["product_types"]:
                    owner_map[o_name]["product_types"][p_type] = 0
                owner_map[o_name]["product_types"][p_type] += val
                
        return {"owners": list(owner_map.values())}
'''
with open('infras/primary_db/repos/order_repo.py', 'a') as f:
    f.write('\n' + repo_code + '\n')

# 2. order_service.py
svc_code = '''
    async def get_owner_sales_report(self, from_date, to_date, date_by):
        from infras.primary_db.repos.order_repo import OrdersRepo
        return await OrdersRepo(session=self.session).get_owner_sales_report(from_date, to_date, date_by, self.cur_user_id, self.user_role)
'''
with open('infras/primary_db/services/order_service.py', 'a') as f:
    f.write('\n' + svc_code + '\n')

# 3. order_handler.py
handler_code = '''
    @catch_errors
    async def get_owner_sales_report(self, data):
        from infras.primary_db.services.order_service import OrdersService
        report = await OrdersService(session=self.session,user_role=self.user_role,cur_user_id=self.cur_user_id).get_owner_sales_report(
            from_date=data.from_date,
            to_date=data.to_date,
            date_by=data.date_by
        )
        return SuccessResponseTypDict(
            detail=BaseResponseTypDict(
                msg="Owner Sales Report Fetched successfully",
                status_code=200,
                success=True
            ),
            data=report
        )
'''
with open('api/handlers/order_handler.py', 'a') as f:
    f.write('\n' + handler_code + '\n')

# 4. api/routes/order.py
route_code = '''
@route.post("/report/owner-sales")
async def get_owner_sales_report(data: OwnerSalesReportSchema, request: Request, bearer_token: str = Depends(oauth2_scheme)):
    return await OrdersHandler(request=request, bearer_token=bearer_token).get_owner_sales_report(data=data)
'''
with open('api/routes/order.py', 'r') as f:
    content = f.read()
if 'OwnerSalesReportSchema' not in content:
    content = content.replace('from schemas.request_schemas.order import ', 'from schemas.request_schemas.order import OwnerSalesReportSchema, ')
with open('api/routes/order.py', 'w') as f:
    f.write(content + '\n' + route_code + '\n')

print('Success')
