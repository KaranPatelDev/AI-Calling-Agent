from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth import require_api_key
from app.db import get_db
from app.models import InboundCall
from app.schemas import InboundCallOut

router = APIRouter(prefix="/api/inbound-calls", tags=["inbound"], dependencies=[Depends(require_api_key)])


@router.get("", response_model=list[InboundCallOut])
def list_inbound_calls(db: Session = Depends(get_db)):
    return db.query(InboundCall).order_by(InboundCall.created_at.desc()).all()
