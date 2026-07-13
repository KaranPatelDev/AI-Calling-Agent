import io
import re

import pandas as pd
import pdfplumber
from fastapi import APIRouter, Depends, HTTPException, UploadFile

from app.auth import require_api_key
from app.schemas import ParsedRecipient

router = APIRouter(prefix="/api", tags=["uploads"], dependencies=[Depends(require_api_key)])

_PHONE_RE = re.compile(r"[+]?[\d][\d\s\-().]{7,}\d")
_NAME_COLS = {"name", "recipient", "recipient_name", "full name"}
_PHONE_COLS = {"phone", "phone_number", "number", "mobile", "contact"}
_ORG_COLS = {"organization", "organisation", "company", "company name", "org", "business", "employer"}


@router.post("/parse-upload", response_model=list[ParsedRecipient])
async def parse_upload(file: UploadFile):
    content = await file.read()
    filename = (file.filename or "").lower()

    if filename.endswith((".xlsx", ".xls")):
        return _parse_excel(content)
    if filename.endswith(".csv"):
        return _parse_excel(content, csv=True)
    if filename.endswith(".pdf"):
        return _parse_pdf(content)
    raise HTTPException(status_code=400, detail="Unsupported file type. Use .xlsx, .csv, or .pdf")


def _parse_excel(content: bytes, csv: bool = False) -> list[ParsedRecipient]:
    df = pd.read_csv(io.BytesIO(content)) if csv else pd.read_excel(io.BytesIO(content))
    df.columns = [str(c).strip().lower() for c in df.columns]

    name_col = next((c for c in df.columns if c in _NAME_COLS), df.columns[0])
    phone_col = next((c for c in df.columns if c in _PHONE_COLS), df.columns[-1])
    org_col = next((c for c in df.columns if c in _ORG_COLS), None)

    recipients = []
    for _, row in df.iterrows():
        name = str(row[name_col]).strip()
        phone = str(row[phone_col]).strip()
        org = str(row[org_col]).strip() if org_col is not None else ""
        if org.lower() == "nan":
            org = ""
        if name and phone and name.lower() != "nan" and phone.lower() != "nan":
            recipients.append(ParsedRecipient(name=name, phone=phone, organization=org or None))
    return recipients


def _parse_pdf(content: bytes) -> list[ParsedRecipient]:
    recipients = []
    with pdfplumber.open(io.BytesIO(content)) as pdf:
        for page in pdf.pages:
            for table in page.extract_tables() or []:
                for row in table:
                    cells = [c.strip() for c in row if c and c.strip()]
                    if len(cells) >= 2:
                        phone_match = _PHONE_RE.search(cells[-1])
                        if phone_match:
                            org = cells[1] if len(cells) >= 3 else None
                            recipients.append(ParsedRecipient(name=cells[0], phone=phone_match.group(), organization=org))
            if not recipients:
                text = page.extract_text() or ""
                for line in text.splitlines():
                    phone_match = _PHONE_RE.search(line)
                    if phone_match:
                        name = line[: phone_match.start()].strip(" ,:-\t")
                        if name:
                            recipients.append(ParsedRecipient(name=name, phone=phone_match.group()))
    return recipients
