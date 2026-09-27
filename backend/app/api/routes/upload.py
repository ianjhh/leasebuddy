# backend/app/api/routes/upload.py

import json
import logging
import uuid

import boto3
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import JSONResponse

from app.api.dependencies import get_db
from app.config import settings
from app.models.lease import LeaseDocument

logger = logging.getLogger(__name__)

router = APIRouter()

ALLOWED_EXTENSIONS = {"pdf", "png", "jpg", "jpeg", "tiff"}

s3 = boto3.client("s3")
sfn = boto3.client("stepfunctions")


@router.post("/", status_code=202)
async def upload_lease(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """Upload a lease document. Validates, stores in S3, and triggers async processing."""
    filename = file.filename or ""
    ext = filename.split(".")[-1].lower() if "." in filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Allowed: {ALLOWED_EXTENSIONS}"
        )

    # Check Content-Length header before reading the full body
    content_length = file.size
    if content_length and content_length > settings.MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size is {settings.MAX_UPLOAD_SIZE_BYTES // (1024 * 1024)}MB."
        )

    contents = await file.read()

    if len(contents) > settings.MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size is {settings.MAX_UPLOAD_SIZE_BYTES // (1024 * 1024)}MB."
        )

    lease_id = uuid.uuid4()
    s3_key = f"uploads/{lease_id}.{ext}"

    # Create DB record immediately
    lease = LeaseDocument(
        id=lease_id,
        filename=filename,
        s3_url=f"s3://{settings.S3_BUCKET_NAME}/{s3_key}",
        status="processing",
        metadata_={"file_size_bytes": len(contents)},
    )
    db.add(lease)
    await db.commit()

    try:
        # Upload to S3
        s3.put_object(
            Bucket=settings.S3_BUCKET_NAME,
            Key=s3_key,
            Body=contents,
        )

        # Trigger Step Functions pipeline
        sfn.start_execution(
            stateMachineArn=settings.STEP_FUNCTION_ARN,
            name=str(lease_id),
            input=json.dumps({
                "detail": {
                    "bucket": {"name": settings.S3_BUCKET_NAME},
                    "object": {"key": s3_key},
                },
            }),
        )
    except Exception:
        logger.exception("Failed to initiate processing for lease %s", lease_id)
        lease.status = "failed"
        await db.commit()
        raise HTTPException(status_code=500, detail="An internal server error occurred while initiating document processing.")

    return JSONResponse(
        status_code=202,
        content={
            "lease_id": str(lease_id),
            "message": "File uploaded. Processing has started.",
            "status": "processing",
        },
    )


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