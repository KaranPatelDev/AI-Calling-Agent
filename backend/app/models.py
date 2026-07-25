import uuid

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID

from app.db import Base


class CallStatus:
    PENDING = "pending"
    SCHEDULED = "scheduled"
    CALLING = "calling"
    COMPLETED = "completed"
    FAILED = "failed"
    NO_ANSWER = "no_answer"
    CANCELLED = "cancelled"
    CUT_OFF = "cut_off"
    VOICEMAIL = "voicemail"


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
    answered_by_machine = Column(Boolean, nullable=False, default=False)
    speech_rate = Column(Integer, nullable=True)  # null = use the global default from AppSettings
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class InboundCallStatus:
    RINGING = "ringing"
    COMPLETED = "completed"


class InboundCall(Base):
    __tablename__ = "inbound_calls"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    from_number = Column(String, nullable=False)
    matched_name = Column(String, nullable=True)
    matched_organization = Column(String, nullable=True)
    provider_call_id = Column(String, nullable=True, index=True)
    status = Column(String, nullable=False, default=InboundCallStatus.RINGING)
    duration_seconds = Column(Integer, nullable=True)
    missed = Column(Boolean, nullable=False, default=False)
    auto_callback_call_id = Column(UUID(as_uuid=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class AppSettings(Base):
    # ponytail: single-row table (id always 1) — this is a single-user app, no need for a per-user settings table.
    __tablename__ = "app_settings"

    id = Column(Integer, primary_key=True)
    buyer_script = Column(Text, nullable=True)
    seller_script = Column(Text, nullable=True)
    speech_rate = Column(Integer, nullable=False, default=79)
    auto_callback_enabled = Column(Boolean, nullable=False, default=True)
    missed_callback_script = Column(Text, nullable=True)


class ScriptTemplate(Base):
    __tablename__ = "script_templates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    script_text = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
