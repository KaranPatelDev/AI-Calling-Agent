import uuid

from sqlalchemy import Column, DateTime, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID

from app.db import Base


class CallStatus:
    PENDING = "pending"
    SCHEDULED = "scheduled"
    CALLING = "calling"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class CallAudience:
    BUYER = "buyer"
    SELLER = "seller"


class Call(Base):
    __tablename__ = "calls"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    recipient_name = Column(String, nullable=False)
    organization = Column(String, nullable=True)
    audience = Column(String, nullable=False, default=CallAudience.BUYER)
    phone_number = Column(String, nullable=False)
    script_text = Column(Text, nullable=False)
    scheduled_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    status = Column(String, nullable=False, default=CallStatus.PENDING)
    provider_call_id = Column(String, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class AppSettings(Base):
    # ponytail: single-row table (id always 1) — this is a single-user app, no need for a per-user settings table.
    __tablename__ = "app_settings"

    id = Column(Integer, primary_key=True)
    buyer_script = Column(Text, nullable=True)
    seller_script = Column(Text, nullable=True)
