from sqlalchemy import String,Column,Integer,text
from datetime import date
from ..main import PG_BASE

class TablesUiLId(PG_BASE):
    __tablename__="table_ui_lid"
    id=Column(String,primary_key=True,server_default="1")
    order_luiid=Column(String)
    product_luiid=Column(String)
    distri_luiid=Column(String)
    contact_luiid=Column(String)
    customer_luiid=Column(String)
    lead_luiid=Column(String)
    oppor_luiid=Column(String)
    user_luiid=Column(String)