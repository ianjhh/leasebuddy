# backend/app/db/session.py

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings

# 1. Create the Engine
# The engine manages the connection pool to the database.
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    future=True
)

# 2. Create the Session Factory
# A session is a single "conversation" with the database.
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Note: The get_db() dependency function lives in app.api.dependencies
# to keep database session management in one canonical location.