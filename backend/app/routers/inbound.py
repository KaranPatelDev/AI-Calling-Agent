from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth import require_api_key
from app.db import get_db
from app.models import Call, InboundCall
from app.schemas import InboundCallOut

router = APIRouter(prefix="/api/inbound-calls", tags=["inbound"], dependencies=[Depends(require_api_key)])


@router.get("", response_model=list[InboundCallOut])
def list_inbound_calls(db: Session = Depends(get_db)):
    inbound_calls = db.query(InboundCall).order_by(InboundCall.created_at.desc()).all()
    out = []
    for row in inbound_calls:
        data = InboundCallOut.model_validate(row).model_dump()
        if row.auto_callback_call_id:
            callback = db.get(Call, row.auto_callback_call_id)
            if callback:
                data["auto_callback_scheduled_at"] = callback.scheduled_at
                data["auto_callback_status"] = callback.status
        out.append(data)
    return out
