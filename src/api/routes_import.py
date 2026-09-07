"""Domain List Batch Import API routes."""

from __future__ import annotations
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from pydantic import BaseModel

from src.importer.domain_importer import DomainImporter


router = APIRouter(prefix="/import", tags=["Import"])


class TextImportRequest(BaseModel):
    domains: Optional[List[str]] = None
    text: Optional[str] = None
    enqueue_verification: bool = True


@router.post("/text")
def import_domains_from_text(req: TextImportRequest):
    if req.domains:
        content = req.domains
    elif req.text:
        content = req.text
    else:
        raise HTTPException(status_code=400, detail="Either 'domains' list or 'text' string is required.")

    result = DomainImporter.import_domains(
        content=content,
        enqueue_verification=req.enqueue_verification,
    )
    return result


@router.post("/file")
async def import_domains_from_file(
    file: UploadFile = File(...),
    enqueue_verification: bool = Form(True),
):
    content = await file.read()
    filename = file.filename or "import.txt"

    result = DomainImporter.import_domains(
        content=content,
        filename=filename,
        enqueue_verification=enqueue_verification,
    )
    return result
