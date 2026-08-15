# backend/app/api/routes/upload.py

import logging
import uuid
from fastapi import APIRouter, File, UploadFile, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict
from app.api.dependencies import get_db
from app.models.lease import LeaseDocument
from app.services.document_processor import process_document
from app.rag.indexer import index_document
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()

ALLOWED_EXTENSIONS = {"pdf", "png", "jpg", "jpeg", "tiff"}

@router.post("/")
async def upload_lease(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, str]:
    """Upload a lease document. Validates, extracts text, chunks, embeds, and saves."""
    filename = file.filename or ""
    ext = filename.split(".")[-1].lower() if "." in filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Allowed: {ALLOWED_EXTENSIONS}"
        )

    contents = await file.read()

    if len(contents) > settings.MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size is {settings.MAX_UPLOAD_SIZE_BYTES // (1024 * 1024)}MB."
        )

    lease = LeaseDocument(
        id=uuid.uuid4(),
        filename=filename,
        status="processing",
        metadata_={"file_size_bytes": len(contents)},
    )
    db.add(lease)
    await db.commit()
    await db.refresh(lease)

    try:
        extracted_pages = await process_document(contents, filename)

        chunk_count = await index_document(
            lease_id=str(lease.id),
            extracted_pages=extracted_pages,
            db=db
        )

        lease.status = "completed"
        lease.metadata_ = {**lease.metadata_, "chunk_count": chunk_count}
        await db.commit()

    except Exception as e:
        logger.exception("Processing failed for lease %s", lease.id)
        lease.status = "failed"
        lease.metadata_ = {**lease.metadata_, "error": str(e)}
        await db.commit()
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")

    return {
        "lease_id": str(lease.id),
        "message": "File uploaded and processed successfully.",
        "status": "completed",
        "chunks_created": str(chunk_count),
    }