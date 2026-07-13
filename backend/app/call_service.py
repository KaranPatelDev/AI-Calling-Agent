import logging

from app.db import SessionLocal
from app.models import Call, CallStatus
from app.plivo_client import place_call

logger = logging.getLogger(__name__)


def execute_call(call_id):
    """Loads a `calls` row and places the Plivo call. Used for both immediate and scheduled calls."""
    db = SessionLocal()
    try:
        call = db.get(Call, call_id)
        if call is None or call.status != CallStatus.PENDING and call.status != CallStatus.SCHEDULED:
            return
        try:
            call_uuid = place_call(call.id, call.phone_number)
            call.status = CallStatus.CALLING
            call.provider_call_id = call_uuid
        except Exception as exc:
            logger.exception("Failed to place call %s", call_id)
            call.status = CallStatus.FAILED
            call.error_message = str(exc)
        db.commit()
    finally:
        db.close()
