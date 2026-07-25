import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel

Audience = Literal["buyer", "seller"]


class Recipient(BaseModel):
    name: str
    phone: str
    organization: str | None = None


class CreateCallsRequest(BaseModel):
    recipients: list[Recipient]
    script_text: str
    audience: Audience
    scheduled_at: datetime | None = None
    speech_rate: int | None = None


class CallOut(BaseModel):
    id: uuid.UUID
    recipient_name: str
    organization: str | None
    audience: str
    phone_number: str
    script_text: str
    scheduled_at: datetime
    status: str
    provider_call_id: str | None
    error_message: str | None
    speech_rate: int | None
    created_at: datetime

    class Config:
        from_attributes = True


class ParsedRecipient(BaseModel):
    name: str
    phone: str
    organization: str | None = None


class ScriptSettings(BaseModel):
    buyer_script: str | None = None
    seller_script: str | None = None
    speech_rate: int = 75
    auto_callback_enabled: bool = True
    missed_callback_script: str | None = None

    class Config:
        from_attributes = True


class InboundCallOut(BaseModel):
    id: uuid.UUID
    from_number: str
    matched_name: str | None
    matched_organization: str | None
    status: str
    duration_seconds: int | None
    missed: bool
    auto_callback_call_id: uuid.UUID | None
    auto_callback_scheduled_at: datetime | None = None
    auto_callback_status: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class ScriptTemplateIn(BaseModel):
    name: str
    script_text: str


class ScriptTemplateOut(BaseModel):
    id: uuid.UUID
    name: str
    script_text: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
