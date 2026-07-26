from datetime import datetime, timedelta, timezone

from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.background import BackgroundScheduler

from app.call_service import execute_call
from app.config import settings
from app.db import SessionLocal
from app.models import InboundCall, InboundCallStatus

scheduler = BackgroundScheduler(
    jobstores={"default": SQLAlchemyJobStore(url=settings.database_url)},
    timezone="UTC",
)

_STALE_RINGING_THRESHOLD = timedelta(minutes=2)


def _mark_stale_ringing_inbound_calls_missed():
    # ponytail: if a caller hangs up before the forwarded leg is answered, Plivo doesn't
    # always fire the Application Hangup URL for that inbound call — leaving the row stuck at
    # "ringing" forever. Sweep periodically and treat anything stuck past a sane timeout as missed.
    db = SessionLocal()
    try:
        cutoff = datetime.now(timezone.utc) - _STALE_RINGING_THRESHOLD
        stale = (
            db.query(InboundCall)
            .filter(InboundCall.status == InboundCallStatus.RINGING, InboundCall.created_at < cutoff)
            .all()
        )
        for row in stale:
            row.status = InboundCallStatus.COMPLETED
            row.missed = True
        if stale:
            db.commit()
    finally:
        db.close()


scheduler.add_job(
    _mark_stale_ringing_inbound_calls_missed,
    trigger="interval",
    minutes=1,
    id="cleanup-stale-inbound-calls",
    replace_existing=True,
)


def schedule_call(call_id, run_at):
    scheduler.add_job(
        execute_call,
        trigger="date",
        run_date=run_at,
        args=[call_id],
        id=f"call-{call_id}",
        replace_existing=True,
        # ponytail: APScheduler's default misfire_grace_time is 1 second — any backend
        # restart (a deploy, a crash) that's still down 1s past the scheduled time causes
        # the job to be silently dropped instead of firing late. None = always fire.
        misfire_grace_time=None,
    )


def cancel_call(call_id):
    scheduler.remove_job(f"call-{call_id}", jobstore="default") if scheduler.get_job(f"call-{call_id}") else None
