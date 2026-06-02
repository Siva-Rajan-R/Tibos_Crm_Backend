from sqlalchemy import select, func, desc, String, or_, cast, Date
from infras.primary_db.models.activity_log import ActivityLog

def test():
    # just print the SQL
    date_expr = func.date(func.timezone("Asia/Kolkata", ActivityLog.created_at))
    stmt = select(ActivityLog)
    stmt = stmt.where(date_expr >= "2026-05-31")
    stmt = stmt.where(date_expr <= "2026-05-31")
    print(stmt)

test()
