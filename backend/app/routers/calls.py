import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import require_api_key
from app.db import get_db
from app.models import Call, CallStatus
from app.schemas import CallOut, CreateCallsRequest
from app.scheduler import cancel_call, schedule_call

router = APIRouter(prefix="/api/calls", tags=["calls"], dependencies=[Depends(require_api_key)])


@router.post("", response_model=list[CallOut])
def create_calls(body: CreateCallsRequest, db: Session = Depends(get_db)):
    now = datetime.now(timezone.utc)
    run_at = body.scheduled_at or now
    is_future = run_at > now
    created = []
    for recipient in body.recipients:
        call = Call(
            recipient_name=recipient.name,
            organization=recipient.organization,
            audience=body.audience,
            phone_number=recipient.phone,
            script_text=body.script_text,
            scheduled_at=run_at,
            status=CallStatus.SCHEDULED if is_future else CallStatus.PENDING,
            speech_rate=body.speech_rate,
        )
        db.add(call)
        created.append(call)
    db.commit()
    # ponytail: schedule jobs only after commit — an immediate "call now" job can fire within
    # milliseconds, and execute_call() loads the row in its own DB session/connection. Scheduling
    # before commit let that background thread race the request's transaction and silently no-op
    # on an uncommitted row, leaving the call stuck at "pending" forever.
    for call in created:
        db.refresh(call)
        schedule_call(call.id, run_at)
    return created


@router.get("", response_model=list[CallOut])
def list_calls(db: Session = Depends(get_db)):
    return db.query(Call).order_by(Call.created_at.desc()).all()


_TERMINAL_STATUSES = (CallStatus.COMPLETED, CallStatus.FAILED, CallStatus.NO_ANSWER, CallStatus.CANCELLED)


@router.delete("/{call_id}")
def delete_call(call_id: uuid.UUID, db: Session = Depends(get_db)):
    """Cancels a pending/scheduled call, or permanently removes a finished one from history."""
    call = db.get(Call, call_id)
    if call is None:
        raise HTTPException(status_code=404, detail="Call not found")

    if call.status in (CallStatus.PENDING, CallStatus.SCHEDULED):
        cancel_call(call.id)
        call.status = CallStatus.CANCELLED
        db.commit()
        db.refresh(call)
        return CallOut.model_validate(call)

    db.delete(call)
    db.commit()
    return {"ok": True}


@router.delete("")
def clear_call_history(db: Session = Depends(get_db)):
    """Permanently deletes all finished calls (completed/failed/no_answer/cancelled)."""
    deleted = db.query(Call).filter(Call.status.in_(_TERMINAL_STATUSES)).delete(synchronize_session=False)
    db.commit()
    return {"deleted": deleted}
