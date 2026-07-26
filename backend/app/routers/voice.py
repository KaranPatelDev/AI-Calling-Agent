import re
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Form
from fastapi.responses import Response
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_db
from app.models import AppSettings, Call, CallStatus, InboundCall, InboundCallStatus
from app.scheduler import schedule_call

router = APIRouter(prefix="/voice", tags=["voice"])

# ponytail: no Plivo request-signature validation yet (ids are random UUIDs, low risk for v1).
# Add Plivo's signature validation here if these endpoints need hardening.

_PLACEHOLDER_RE = re.compile(r"\{\{\s*(name|company|organization)\s*\}\}", re.IGNORECASE)
_SLOW_RE = re.compile(r"\[\[slow\]\](.*?)\[\[/slow\]\]", re.IGNORECASE | re.DOTALL)
_MISSED_CALLBACK_SECONDS = 10  # a forwarded callback lasting this long or less counts as missed


def _render_script(call: Call) -> str:
    def replace(match):
        key = match.group(1).lower()
        return call.recipient_name if key == "name" else (call.organization or "")

    return _PLACEHOLDER_RE.sub(replace, call.script_text)


def _add_natural_pauses(ssml_fragment: str) -> str:
    # ponytail: standard (non-neural) Polly voices have no expressiveness controls beyond
    # rate/pitch — short breaks after punctuation are the main lever left to make delivery
    # sound paced/natural instead of a flat, rushed readout. Safe to run on the whole fragment
    # since our escaped text/tags never contain literal '.', '!', '?', or ',' inside a tag.
    ssml_fragment = re.sub(r'([.!?])(\s|$)', r'\1<break time="300ms"/>\2', ssml_fragment)
    ssml_fragment = re.sub(r"(,)(\s|$)", r'\1<break time="150ms"/>\2', ssml_fragment)
    return ssml_fragment


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
    return _add_natural_pauses("".join(parts))


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
    script = _render_script(call) if call else ""
    rate = _get_speech_rate(db, call)
    body = _build_ssml_body(script)
    # ponytail: Polly.Aditi (standard engine) is the only Hindi voice Plivo reliably supports —
    # Kajal (neural) and Google/ElevenLabs alternatives were tried and reverted. Pushed the two
    # remaining levers as far as reasonable: a modest pitch lift for warmth (much beyond +10%
    # starts sounding unnatural/chipmunky) and natural pauses after punctuation (_build_ssml_body)
    # so delivery paces like speech instead of a flat, rushed readout.
    plivo_xml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<Response><Speak voice="Polly.Aditi" language="hi-IN">'
        f'<prosody rate="{rate}%" pitch="+10%">{body}</prosody>'
        "</Speak></Response>"
    )
    return Response(content=plivo_xml, media_type="application/xml")


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


@router.post("/inbound-hangup")
def inbound_hangup(
    CallUUID: str = Form(default=""),
    Duration: str = Form(default=""),
    db: Session = Depends(get_db),
):
    """Static hangup callback for inbound calls (no per-call id exists until Plivo posts CallUUID)."""
    inbound = db.query(InboundCall).filter(InboundCall.provider_call_id == CallUUID).first()
    if inbound:
        duration = int(Duration) if Duration.isdigit() else 0
        inbound.status = InboundCallStatus.COMPLETED
        inbound.duration_seconds = duration if Duration.isdigit() else None
        # ponytail: a forwarded callback that connects but lasts 5s or less is effectively a
        # miss (rang, no real conversation happened) — duration is a more reliable signal here
        # than HangupCause, which reports NORMAL_CLEARING even for very short answered calls.
        inbound.missed = duration <= _MISSED_CALLBACK_SECONDS
        db.commit()
    return {"ok": True}


def _next_retry_time(now: datetime) -> datetime:
    run_at = now + timedelta(hours=24)
    if run_at.weekday() == 6:  # Sunday -> push to Monday same time
        run_at += timedelta(days=1)
    return run_at


def _schedule_no_answer_retry(call: Call, db: Session):
    # ponytail: retries only the original call, never a retry of a retry — avoids an
    # indefinite daily-retry chain if the recipient still doesn't pick up the second time.
    if call.is_retry or call.retry_call_id is not None:
        return
    app_settings = db.get(AppSettings, 1)
    if app_settings and not app_settings.auto_callback_enabled:
        return

    run_at = _next_retry_time(datetime.now(timezone.utc))
    retry_call = Call(
        recipient_name=call.recipient_name,
        organization=call.organization,
        audience=call.audience,
        phone_number=call.phone_number,
        script_text=call.script_text,
        scheduled_at=run_at,
        status=CallStatus.SCHEDULED,
        speech_rate=call.speech_rate,
        is_retry=True,
    )
    db.add(retry_call)
    db.flush()
    schedule_call(retry_call.id, run_at)
    call.retry_call_id = retry_call.id


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
        if status == CallStatus.NO_ANSWER:
            _schedule_no_answer_retry(call, db)

    db.commit()
    return {"ok": True}


def _escape(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )
