# backend/app/main.py

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import health, upload, chat
from app.api.middleware import RequestLoggingMiddleware
from app.db.session import engine
from app.models.base import Base

# Import all models so SQLAlchemy knows about them when we call create_all.
# Without this import, Base.metadata has zero tables and nothing gets created.
import app.models.lease  # noqa: F401

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    The lifespan context manager.
    Code before the 'yield' runs when the application STARTS UP.
    Code after the 'yield' runs when the application SHUTS DOWN.
    """
    # ── Startup ──────────────────────────────────────────────────────────
    print("Starting up LeaseGPT backend...")

    # Create all database tables that don't already exist.
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Database tables verified / created.")

    # ── Application runs ─────────────────────────────────────────────────
    yield

    # ── Shutdown ─────────────────────────────────────────────────────────
    await engine.dispose()
    print("Shutting down LeaseGPT backend... Connection pool closed.")

app = FastAPI(
    title="LeaseGPT API",
    description="API for uploading leases and chatting with them via RAG",
    version="1.0.0",
    lifespan=lifespan
)

# ── Middleware ────────────────────────────────────────────────────────────────
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(health.router, prefix="/health", tags=["Health"])
app.include_router(upload.router, prefix="/api/leases", tags=["Upload"])
app.include_router(chat.router, tags=["Chat"])

@app.get("/")
async def root():
    """A simple default route just to show the server is alive."""
    return {"message": "Welcome to the LeaseGPT API!"}