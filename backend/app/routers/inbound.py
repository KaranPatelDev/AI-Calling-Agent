import io

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.auth import require_api_key
from app.db import get_db
from app.models import InboundCall
from app.schemas import InboundCallOut

router = APIRouter(prefix="/api/inbound-calls", tags=["inbound"], dependencies=[Depends(require_api_key)])


@router.get("", response_model=list[InboundCallOut])
def list_inbound_calls(db: Session = Depends(get_db)):
    return db.query(InboundCall).order_by(InboundCall.created_at.desc()).all()


@router.get("/export")
def export_inbound_calls(filter: str = "missed", db: Session = Depends(get_db)):
    if filter not in ("missed", "completed"):
        raise HTTPException(status_code=400, detail="Invalid filter")

    rows = (
        db.query(InboundCall)
        .filter(InboundCall.missed == (filter == "missed"))
        .order_by(InboundCall.created_at.desc())
        .all()
    )
    df = pd.DataFrame(
        [
            {
                "Name": r.matched_name or "Unknown caller",
                "Organization": r.matched_organization or "",
                "Contact Number": r.from_number,
            }
            for r in rows
        ],
        columns=["Name", "Organization", "Contact Number"],
    )
    buffer = io.BytesIO()
    df.to_excel(buffer, index=False, engine="openpyxl")
    buffer.seek(0)
    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="callbacks_{filter}.xlsx"'},
    )
