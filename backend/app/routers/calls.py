import io
import uuid
from datetime import datetime, timezone

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.auth import require_api_key
from app.db import get_db
from app.models import Call, CallStatus
from app.schemas import CallOut, CreateCallsRequest
from app.scheduler import cancel_call, schedule_call

router = APIRouter(prefix="/api/calls", tags=["calls"], dependencies=[Depends(require_api_key)])

# ponytail: export/bulk-delete filters deliberately exclude "completed" — these are the
# outcomes worth re-working (retry later, fix the number, re-schedule), not a success list.
_FILTER_STATUSES = {
    "failed": [CallStatus.FAILED],
    "cut_off": [CallStatus.CUT_OFF],
    "no_answer": [CallStatus.NO_ANSWER],
    "scheduled": [CallStatus.SCHEDULED, CallStatus.PENDING],
}
_FILTER_STATUSES["all"] = [s for statuses in _FILTER_STATUSES.values() for s in statuses]


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
    calls = db.query(Call).order_by(Call.created_at.desc()).all()
    out = []
    for row in calls:
        data = CallOut.model_validate(row).model_dump()
        if row.retry_call_id:
            retry = db.get(Call, row.retry_call_id)
            if retry:
                data["retry_scheduled_at"] = retry.scheduled_at
                data["retry_status"] = retry.status
        out.append(data)
    return out


@router.get("/export")
def export_calls(filter: str = "all", db: Session = Depends(get_db)):
    statuses = _FILTER_STATUSES.get(filter)
    if statuses is None:
        raise HTTPException(status_code=400, detail="Invalid filter")

    rows = db.query(Call).filter(Call.status.in_(statuses)).order_by(Call.created_at.desc()).all()
    df = pd.DataFrame(
        [{"Name": r.recipient_name, "Organization": r.organization or "", "Contact Number": r.phone_number} for r in rows],
        columns=["Name", "Organization", "Contact Number"],
    )
    buffer = io.BytesIO()
    df.to_excel(buffer, index=False, engine="openpyxl")
    buffer.seek(0)
    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="calls_{filter}.xlsx"'},
    )


_TERMINAL_STATUSES = (CallStatus.COMPLETED, CallStatus.FAILED, CallStatus.NO_ANSWER, CallStatus.CANCELLED)

# ponytail: mirrors Dashboard.jsx's OUTCOME_OPTIONS values exactly — separate from
# _FILTER_STATUSES above (export intentionally excludes "completed"; delete-all covers every tab).
_OUTCOME_DELETE_STATUSES = {
    "completed": [CallStatus.COMPLETED],
    "failed": [CallStatus.FAILED],
    "no_answer": [CallStatus.NO_ANSWER],
    "cut_off": [CallStatus.CUT_OFF],
    "scheduled": [CallStatus.SCHEDULED, CallStatus.PENDING],
}


@router.delete("/bulk")
def delete_calls_bulk(outcome: str = "all", audience: str | None = None, db: Session = Depends(get_db)):
    """Deletes every call matching a single outcome tab (and optionally audience) — used by the
    Dashboard's per-tab "Delete all" button, scoped to only what's currently on screen."""
    query = db.query(Call)
    if outcome != "all":
        statuses = _OUTCOME_DELETE_STATUSES.get(outcome)
        if statuses is None:
            raise HTTPException(status_code=400, detail="Invalid outcome filter")
        query = query.filter(Call.status.in_(statuses))
    if audience and audience != "all":
        query = query.filter(Call.audience == audience)

    rows = query.all()
    for call in rows:
        if call.status in (CallStatus.PENDING, CallStatus.SCHEDULED):
            cancel_call(call.id)
        db.delete(call)
    db.commit()
    return {"deleted": len(rows)}


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
