from sqlalchemy import String,Column,ForeignKey,func,TIMESTAMP,JSON
from sqlalchemy.dialects.postgresql import JSONB
from ..main import PG_BASE

class ActivityLog(PG_BASE):
    __tablename__ = "activity_logs"
    id = Column(String, primary_key=True)
    user_id = Column(String, nullable=False)
    action = Column(String, nullable=False)
    entity_type = Column(String, nullable=False)
    entity_id = Column(String, nullable=False)
    details = Column(JSONB, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
