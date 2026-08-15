# backend/app/api/routes/health.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.api.dependencies import get_db

router = APIRouter()

@router.get("/")
async def liveness_check() -> dict:
    """Liveness probe. Returns 200 if the server is running."""
    return {"status": "alive"}

@router.get("/ready")
async def readiness_check(session: AsyncSession = Depends(get_db)) -> dict:
    """Readiness probe. Checks if the database is reachable."""
    try:
        await session.execute(text("SELECT 1"))
        return {"status": "ready", "database": "connected"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Database unavailable: {str(e)}")