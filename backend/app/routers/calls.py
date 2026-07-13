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
        )
        db.add(call)
        db.flush()
        schedule_call(call.id, run_at)
        created.append(call)
    db.commit()
    for call in created:
        db.refresh(call)
    return created


@router.get("", response_model=list[CallOut])
def list_calls(db: Session = Depends(get_db)):
    return db.query(Call).order_by(Call.created_at.desc()).all()


@router.delete("/{call_id}", response_model=CallOut)
def cancel_scheduled_call(call_id: uuid.UUID, db: Session = Depends(get_db)):
    call = db.get(Call, call_id)
    if call is None:
        raise HTTPException(status_code=404, detail="Call not found")
    if call.status not in (CallStatus.PENDING, CallStatus.SCHEDULED):
        raise HTTPException(status_code=400, detail="Only pending/scheduled calls can be cancelled")
    cancel_call(call.id)
    call.status = CallStatus.CANCELLED
    db.commit()
    db.refresh(call)
    return call
