from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth import require_api_key
from app.db import get_db
from app.models import AppSettings
from app.schemas import ScriptSettings

router = APIRouter(prefix="/api/settings", tags=["settings"], dependencies=[Depends(require_api_key)])


def _get_or_create(db: Session) -> AppSettings:
    row = db.get(AppSettings, 1)
    if row is None:
        row = AppSettings(id=1)
        db.add(row)
        db.commit()
        db.refresh(row)
    return row


@router.get("/scripts", response_model=ScriptSettings)
def get_scripts(db: Session = Depends(get_db)):
    return _get_or_create(db)


@router.put("/scripts", response_model=ScriptSettings)
def update_scripts(body: ScriptSettings, db: Session = Depends(get_db)):
    row = _get_or_create(db)
    row.buyer_script = body.buyer_script
    row.seller_script = body.seller_script
    db.commit()
    db.refresh(row)
    return row
