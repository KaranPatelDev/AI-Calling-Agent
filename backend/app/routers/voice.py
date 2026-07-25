import logging
import re
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Form, HTTPException
from fastapi.responses import Response
from sqlalchemy import func
from sqlalchemy.orm import Session

from app import audio_cache
from app.config import settings
from app.db import get_db
from app.google_tts import synthesize
from app.models import AppSettings, Call, CallStatus, InboundCall, InboundCallStatus
from app.scheduler import schedule_call

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/voice", tags=["voice"])

# ponytail: no Plivo request-signature validation yet (ids are random UUIDs, low risk for v1).
# Add Plivo's signature validation here if these endpoints need hardening.

_PLACEHOLDER_RE = re.compile(r"\{\{\s*(name|company|organization)\s*\}\}", re.IGNORECASE)
_SLOW_RE = re.compile(r"\[\[slow\]\](.*?)\[\[/slow\]\]", re.IGNORECASE | re.DOTALL)
_MISSED_HANGUP_CAUSES = {"NO_ANSWER", "USER_BUSY", "CALL_REJECTED", "NO_USER_RESPONSE", "NO_ANSWER_TIMEOUT"}


def _render_script(call: Call) -> str:
    def replace(match):
        key = match.group(1).lower()
        return call.recipient_name if key == "name" else (call.organization or "")

    return _PLACEHOLDER_RE.sub(replace, call.script_text)


def _build_ssml_body(text: str) -> str:
    """Converts [[slow]]...[[/slow]] markers into a nested slower <prosody>, escaping plain segments."""
    parts = []
    last = 0
    for m in _SLOW_RE.finditer(text):
        if m.start() > last:
            parts.append(_escape(text[last : m.start()]))
        parts.append(f'<prosody rate="65%">{_escape(m.group(1))}</prosody>')
        last = m.end()
    parts.append(_escape(text[last:]))
    return "".join(parts)


def _get_speech_rate(db: Session, call: Call | None = None) -> int:
    if call is not None and call.speech_rate is not None:
        return call.speech_rate
    row = db.get(AppSettings, 1)
    return row.speech_rate if row else 79


def _estimate_speech_seconds(text: str, rate_pct: int) -> float:
    # ponytail: rough word-count heuristic (~150 wpm at 100% rate), not a precise TTS timing model.
    words = len(re.findall(r"\S+", _SLOW_RE.sub(r"\1", text)))
    wpm = 150 * (rate_pct / 100) if rate_pct else 150
    return (words / wpm) * 60 if wpm > 0 else 0


@router.post("/answer/{call_id}")
def answer(call_id: uuid.UUID, db: Session = Depends(get_db)):
    call = db.get(Call, call_id)

    if call and call.direct_connect:
        # ponytail: a missed-callback retry dials the person straight through to your real
        # phone — no AI script, exactly like a normal human-to-human call.
        plivo_xml = (
            '<?xml version="1.0" encoding="UTF-8"?>'
            f'<Response><Dial callerId="{settings.plivo_from_number}">'
            f'<Number>{settings.forward_to_number}</Number>'
            "</Dial></Response>"
        )
        return Response(content=plivo_xml, media_type="application/xml")

    script = _render_script(call) if call else ""
    rate = _get_speech_rate(db, call)
    body = _build_ssml_body(script)

    try:
        ssml = f'<speak><prosody rate="{rate}%">{body}</prosody></speak>'
        audio_cache.put(call_id, synthesize(ssml))
        base = settings.public_base_url.rstrip("/")
        plivo_xml = (
            '<?xml version="1.0" encoding="UTF-8"?>'
            f"<Response><Play>{base}/voice/audio/{call_id}</Play></Response>"
        )
    except Exception:
        # ponytail: Google TTS being down/misconfigured shouldn't kill the call — fall back to
        # Plivo's built-in voice so the script still gets read, just in a lower-quality voice.
        logger.exception("Google TTS synthesis failed for call %s, falling back to Plivo voice", call_id)
        plivo_xml = (
            '<?xml version="1.0" encoding="UTF-8"?>'
            f'<Response><Speak voice="WOMAN" language="hi-IN">{_escape(script)}</Speak></Response>'
        )
    return Response(content=plivo_xml, media_type="application/xml")


@router.get("/audio/{call_id}")
def get_audio(call_id: uuid.UUID):
    data = audio_cache.get(call_id)
    if data is None:
        raise HTTPException(status_code=404, detail="Audio not found or already played")
    return Response(content=data, media_type="audio/mpeg")


@router.post("/machine-detection/{call_id}")
def machine_detection(call_id: uuid.UUID, Machine: str = Form(default=""), db: Session = Depends(get_db)):
    call = db.get(Call, call_id)
    if call:
        call.answered_by_machine = Machine.lower() == "true"
        db.commit()
    return {"ok": True}


@router.post("/inbound")
def inbound_call(
    From: str = Form(default=""),
    CallUUID: str = Form(default=""),
    db: Session = Depends(get_db),
):
    """Logs the callback (for interest tracking) and forwards it to your real phone."""
    # ponytail: Plivo's From arrives without a "+" (e.g. "918160911006") while Call.phone_number
    # is stored E.164 ("+918160911006") — match on digits only so callbacks resolve to a name.
    from_digits = re.sub(r"\D", "", From)
    match = (
        db.query(Call)
        .filter(func.regexp_replace(Call.phone_number, r"\D", "", "g") == from_digits)
        .order_by(Call.created_at.desc())
        .first()
    )
    db.add(
        InboundCall(
            from_number=From,
            matched_name=match.recipient_name if match else None,
            matched_organization=match.organization if match else None,
            provider_call_id=CallUUID,
        )
    )
    db.commit()

    plivo_xml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        f'<Response><Dial callerId="{settings.plivo_from_number}">'
        f'<Number>{settings.forward_to_number}</Number>'
        "</Dial></Response>"
    )
    return Response(content=plivo_xml, media_type="application/xml")


def _next_callback_time(now: datetime) -> datetime:
    run_at = now + timedelta(hours=24)
    if run_at.weekday() == 6:  # Sunday -> push to Monday same time
        run_at += timedelta(days=1)
    return run_at


def _schedule_missed_callback(inbound: InboundCall, db: Session):
    app_settings = db.get(AppSettings, 1)
    if app_settings and not app_settings.auto_callback_enabled:
        return
    if inbound.auto_callback_call_id is not None:
        return  # already scheduled for this inbound call

    run_at = _next_callback_time(datetime.now(timezone.utc))
    callback_call = Call(
        recipient_name=inbound.matched_name or "Unknown caller",
        organization=inbound.matched_organization,
        audience="buyer",
        phone_number=inbound.from_number,
        script_text="",
        scheduled_at=run_at,
        status=CallStatus.SCHEDULED,
        direct_connect=True,
    )
    db.add(callback_call)
    db.flush()
    schedule_call(callback_call.id, run_at)
    inbound.auto_callback_call_id = callback_call.id


@router.post("/inbound-hangup")
def inbound_hangup(
    CallUUID: str = Form(default=""),
    Duration: str = Form(default=""),
    HangupCause: str = Form(default=""),
    db: Session = Depends(get_db),
):
    """Static hangup callback for inbound calls (no per-call id exists until Plivo posts CallUUID)."""
    inbound = db.query(InboundCall).filter(InboundCall.provider_call_id == CallUUID).first()
    if inbound:
        inbound.status = InboundCallStatus.COMPLETED
        inbound.duration_seconds = int(Duration) if Duration.isdigit() else None
        inbound.missed = HangupCause in _MISSED_HANGUP_CAUSES
        if inbound.missed:
            _schedule_missed_callback(inbound, db)
        db.commit()
    return {"ok": True}


_HANGUP_OUTCOMES = {
    "NO_ANSWER": (CallStatus.NO_ANSWER, "No answer from recipient"),
    "USER_BUSY": (CallStatus.NO_ANSWER, "Recipient's line was busy"),
    "CALL_REJECTED": (CallStatus.NO_ANSWER, "Call was rejected by recipient"),
    "NO_USER_RESPONSE": (CallStatus.NO_ANSWER, "No response from recipient"),
    "NO_ANSWER_TIMEOUT": (CallStatus.NO_ANSWER, "No response from recipient"),
}


@router.post("/hangup/{call_id}")
def hangup(
    call_id: uuid.UUID,
    HangupCause: str = Form(default=""),
    Duration: str = Form(default=""),
    db: Session = Depends(get_db),
):
    audio_cache.discard(call_id)

    call = db.get(Call, call_id)
    if not call:
        return {"ok": True}

    if HangupCause == "NORMAL_CLEARING":
        rate = _get_speech_rate(db, call)
        estimated = _estimate_speech_seconds(call.script_text, rate)
        actual = int(Duration) if Duration.isdigit() else None
        cut_off = estimated > 3 and actual is not None and actual < estimated * 0.7

        if cut_off:
            call.status = CallStatus.CUT_OFF
            call.error_message = f"Recipient hung up early (~{actual}s of an estimated ~{int(estimated)}s)"
        else:
            # ponytail: Plivo's machine detection isn't reliable enough on Hindi speech to
            # trust for the outcome status — keep recording call.answered_by_machine from its
            # webhook, but don't let it flip a completed call to "voicemail" in the UI.
            call.status = CallStatus.COMPLETED
            call.error_message = None
    else:
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
