from sqlalchemy import String,Integer,Float,Boolean,Column,ForeignKey,ARRAY,BigInteger,Identity,func,TIMESTAMP
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from ..main import PG_BASE



class Opportunities(PG_BASE):
    __tablename__ = "opportunities"

    id = Column(String, primary_key=True)
    sequence_id=Column(Integer,Identity(always=True),nullable=False)
    lead_id = Column(
        String,
        ForeignKey("leads.id", ondelete="CASCADE"),
        nullable=False,
        unique=False
    )

    name = Column(String, nullable=False)
    product = Column(String, nullable=False)

    billing_type = Column(String, nullable=False)

    status = Column(String, nullable=False)

    deal_value = Column(Integer, nullable=False)

    description = Column(String,nullable=True)

    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    # relationship
    lead = relationship("Leads", back_populates="opportunity")