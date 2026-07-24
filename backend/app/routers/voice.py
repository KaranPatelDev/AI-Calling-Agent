import re
import uuid

from fastapi import APIRouter, Depends, Form
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_db
from app.models import Call, CallStatus

router = APIRouter(prefix="/voice", tags=["voice"])

# ponytail: no Plivo request-signature validation yet (ids are random UUIDs, low risk for v1).
# Add Plivo's signature validation here if these endpoints need hardening.

_PLACEHOLDER_RE = re.compile(r"\{\{\s*(name|company|organization)\s*\}\}", re.IGNORECASE)


def _render_script(call: Call) -> str:
    def replace(match):
        key = match.group(1).lower()
        return call.recipient_name if key == "name" else (call.organization or "")

    return _PLACEHOLDER_RE.sub(replace, call.script_text)


@router.post("/answer/{call_id}")
def answer(call_id: uuid.UUID, db: Session = Depends(get_db)):
    script = _render_script(call) if (call := db.get(Call, call_id)) else ""
    plivo_xml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<Response><Speak voice="Polly.Aditi" language="en-IN">'
        f'<prosody rate="90%">{_escape(script)}</prosody>'
        "</Speak></Response>"
    )
    return Response(content=plivo_xml, media_type="application/xml")


@router.post("/inbound")
def inbound_call():
    """Forwards any call to the Plivo number straight to your real phone."""
    plivo_xml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        f'<Response><Dial callerId="{settings.plivo_from_number}">'
        f'<Number>{settings.forward_to_number}</Number>'
        "</Dial></Response>"
    )
    return Response(content=plivo_xml, media_type="application/xml")


_HANGUP_OUTCOMES = {
    "NORMAL_CLEARING": (CallStatus.COMPLETED, None),
    "NO_ANSWER": (CallStatus.NO_ANSWER, "No answer from recipient"),
    "USER_BUSY": (CallStatus.NO_ANSWER, "Recipient's line was busy"),
    "CALL_REJECTED": (CallStatus.NO_ANSWER, "Call was rejected by recipient"),
}


@router.post("/hangup/{call_id}")
def hangup(call_id: uuid.UUID, HangupCause: str = Form(default=""), db: Session = Depends(get_db)):
    call = db.get(Call, call_id)
    if call:
        status, error_message = _HANGUP_OUTCOMES.get(
            HangupCause, (CallStatus.FAILED, f"Call ended unexpectedly ({HangupCause or 'unknown reason'})")
        )
        call.status = status
        call.error_message = error_message
        db.commit()
    return {"ok": True}


def _escape(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )
