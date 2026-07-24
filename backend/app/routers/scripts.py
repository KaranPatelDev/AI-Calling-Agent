import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import require_api_key
from app.db import get_db
from app.models import ScriptTemplate
from app.schemas import ScriptTemplateIn, ScriptTemplateOut

router = APIRouter(prefix="/api/scripts", tags=["scripts"], dependencies=[Depends(require_api_key)])


@router.get("", response_model=list[ScriptTemplateOut])
def list_scripts(db: Session = Depends(get_db)):
    return db.query(ScriptTemplate).order_by(ScriptTemplate.name).all()


@router.post("", response_model=ScriptTemplateOut)
def create_script(body: ScriptTemplateIn, db: Session = Depends(get_db)):
    template = ScriptTemplate(name=body.name, script_text=body.script_text)
    db.add(template)
    db.commit()
    db.refresh(template)
    return template


@router.put("/{script_id}", response_model=ScriptTemplateOut)
def update_script(script_id: uuid.UUID, body: ScriptTemplateIn, db: Session = Depends(get_db)):
    template = db.get(ScriptTemplate, script_id)
    if template is None:
        raise HTTPException(status_code=404, detail="Script not found")
    template.name = body.name
    template.script_text = body.script_text
    db.commit()
    db.refresh(template)
    return template


@router.delete("/{script_id}")
def delete_script(script_id: uuid.UUID, db: Session = Depends(get_db)):
    template = db.get(ScriptTemplate, script_id)
    if template is None:
        raise HTTPException(status_code=404, detail="Script not found")
    db.delete(template)
    db.commit()
    return {"ok": True}
