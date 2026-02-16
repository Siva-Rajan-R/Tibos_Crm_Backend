from datetime import date,datetime

from_date="2025-01-01"
print(datetime.strptime(from_date,"%Y-%m-%d").date()+365)