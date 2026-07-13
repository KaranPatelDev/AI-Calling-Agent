import re
import uuid

from fastapi import APIRouter, Depends, Form
from fastapi.responses import Response
from sqlalchemy.orm import Session

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
    plivo_xml = f'<?xml version="1.0" encoding="UTF-8"?><Response><Speak>{_escape(script)}</Speak></Response>'
    return Response(content=plivo_xml, media_type="application/xml")


@router.post("/hangup/{call_id}")
def hangup(call_id: uuid.UUID, HangupCause: str = Form(default=""), db: Session = Depends(get_db)):
    call = db.get(Call, call_id)
    if call:
        call.status = CallStatus.COMPLETED if HangupCause == "NORMAL_CLEARING" else CallStatus.FAILED
        db.commit()
    return {"ok": True}


def _escape(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )
