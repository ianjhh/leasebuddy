# backend/app/main.py

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import all models so SQLAlchemy knows about them when we call create_all.
import app.models.lease
from app.api.middleware import RequestLoggingMiddleware
from app.api.routes import chat, health, upload
from app.config import settings
from app.db.session import engine
from app.models.base import Base

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    The lifespan context manager.
    Code before the 'yield' runs when the application STARTS UP.
    Code after the 'yield' runs when the application SHUTS DOWN.
    """
    # ── Startup ──────────────────────────────────────────────────────────
    logger.info("Starting up LeaseBuddy backend...")

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables verified / created.")

    # ── Application runs ─────────────────────────────────────────────────
    yield

    # ── Shutdown ─────────────────────────────────────────────────────────
    await engine.dispose()
    logger.info("Shutting down LeaseBuddy backend... Connection pool closed.")

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="API for uploading leases and chatting with them via RAG",
    version="1.0.0",
    lifespan=lifespan
)

# ── Middleware ────────────────────────────────────────────────────────────────
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(health.router, prefix="/health", tags=["Health"])
app.include_router(upload.router, prefix="/api/leases", tags=["Upload"])
app.include_router(chat.router, tags=["Chat"])

@app.get("/")
async def root() -> dict:
    """A simple default route just to show the server is alive."""
    return {"message": "Welcome to the LeaseBuddy API!"}