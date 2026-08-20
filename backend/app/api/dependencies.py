# backend/app/api/dependencies.py

from collections.abc import AsyncGenerator

import redis.asyncio as redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.session import AsyncSessionLocal


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency to get a database session.
    'async with' opens a connection from the pool and hands it to the route via 'yield'.
    When the route finishes, the session is closed automatically.
    """
    async with AsyncSessionLocal() as session:
        yield session

async def get_redis() -> AsyncGenerator[redis.Redis, None]:
    """
    Dependency to get a Redis connection.
    'try/finally' ensures the connection is always closed.
    """
    client = redis.from_url(settings.REDIS_URL, encoding="utf-8", decode_responses=True)
    try:
        yield client
    finally:
        await client.aclose()