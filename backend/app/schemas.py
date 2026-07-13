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

    class Config:
        from_attributes = True
