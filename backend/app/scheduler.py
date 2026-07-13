from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.background import BackgroundScheduler

from app.call_service import execute_call
from app.config import settings

scheduler = BackgroundScheduler(
    jobstores={"default": SQLAlchemyJobStore(url=settings.database_url)},
    timezone="UTC",
)


def schedule_call(call_id, run_at):
    scheduler.add_job(
        execute_call,
        trigger="date",
        run_date=run_at,
        args=[call_id],
        id=f"call-{call_id}",
        replace_existing=True,
    )


def cancel_call(call_id):
    scheduler.remove_job(f"call-{call_id}", jobstore="default") if scheduler.get_job(f"call-{call_id}") else None
