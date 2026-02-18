from sqlalchemy import String,Integer,Float,Boolean,Column,ForeignKey,ARRAY,BigInteger,Identity,func,TIMESTAMP,text,DateTime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from ..main import PG_BASE

class Leads(PG_BASE):
    __tablename__ = "leads"

    id = Column(String, primary_key=True)
    ui_id=Column(String,nullable=True)
    sequence_id=Column(Integer,Identity(always=True),nullable=False)
    name = Column(String, nullable=False)
    email = Column(String,nullable=False)
    phone = Column(String, nullable=False)
    source = Column(String, nullable=False)
    status = Column(String,nullable=False)
    assigned_to = Column(String, nullable=True)
    description = Column(String,nullable=True)

    last_contacted = Column(TIMESTAMP(timezone=True))
    next_followup = Column(TIMESTAMP(timezone=True))

    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    is_deleted=Column(Boolean,server_default=text("false"),nullable=False)
    deleted_by=Column(String,ForeignKey('users.id'))
    deleted_at=Column(DateTime(timezone=True),nullable=True)

    # relationship
    opportunity = relationship("Opportunities",back_populates="lead",uselist=False)