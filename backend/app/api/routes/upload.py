# backend/app/api/routes/upload.py

import logging
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db
from app.config import settings
from app.models.lease import LeaseDocument
from app.rag.indexer import index_document
from app.services.document_processor import process_document

logger = logging.getLogger(__name__)

router = APIRouter()

ALLOWED_EXTENSIONS = {"pdf", "png", "jpg", "jpeg", "tiff"}

@router.post("/")
async def upload_lease(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
) -> dict[str, str]:
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
        # BEST PRACTICE: Never expose internal Python exception messages to the client in production!
        # It can leak file paths, database schemas, or API keys. Log the error (done above), 
        # but return a generic, safe message to the user.
        raise HTTPException(status_code=500, detail="An internal server error occurred while processing the document.")

    return {
        "lease_id": str(lease.id),
        "message": "File uploaded and processed successfully.",
        "status": "completed",
        "chunks_created": str(chunk_count),
    }


@router.get("/{lease_id}")
async def get_lease(
    lease_id: str,
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Get the status of a lease document by ID."""
    try:
        lease_uuid = uuid.UUID(lease_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid lease ID format.")

    result = await db.execute(
        select(LeaseDocument).where(LeaseDocument.id == lease_uuid)
    )
    lease = result.scalar_one_or_none()

    if not lease:
        raise HTTPException(status_code=404, detail="Lease not found.")

    return {
        "lease_id": str(lease.id),
        "filename": lease.filename,
        "status": lease.status,
        "metadata": lease.metadata_,
    }