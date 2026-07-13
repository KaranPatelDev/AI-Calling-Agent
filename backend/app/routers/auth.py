import hmac

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.config import settings

router = APIRouter(prefix="/api", tags=["auth"])


class LoginRequest(BaseModel):
    email: str
    password: str


# ponytail: single hardcoded admin login (matches the existing single-user/shared-API_KEY
# scope), not a users table. Add one if multi-user login is ever needed.
@router.post("/login")
def login(body: LoginRequest):
    email_ok = hmac.compare_digest(body.email.strip().lower(), settings.admin_email.strip().lower())
    password_ok = hmac.compare_digest(body.password, settings.admin_password)
    if not (email_ok and password_ok):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return {"api_key": settings.api_key}
