# backend/app/api/middleware.py

import logging
import time

import redis.asyncio as redis
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, Response

from app.config import settings

logger = logging.getLogger(__name__)

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Logs every incoming request and how long it took to process."""
    async def dispatch(self, request: Request, call_next) -> Response:
        start_time = time.time()
        logger.info("Incoming Request: %s %s", request.method, request.url.path)
        
        response = await call_next(request)
        
        process_time = time.time() - start_time
        logger.info("Completed Request: %s %s in %.4f secs", request.method, request.url.path, process_time)
        response.headers["X-Process-Time"] = str(process_time)
        return response

class SimpleRateLimitMiddleware(BaseHTTPMiddleware):
    """
    Sliding-window rate limiter using Redis.
    Allows at most `max_requests` requests per `window_seconds` per client IP.
    """
    def __init__(self, app, max_requests: int = 60, window_seconds: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.redis = redis.from_url(settings.REDIS_URL, encoding="utf-8", decode_responses=True)

    async def dispatch(self, request: Request, call_next) -> Response:
        client_ip = request.client.host
        now = time.time()
        window_start = now - self.window_seconds
        key = f"rate_limit:{client_ip}"

        async with self.redis.pipeline(transaction=True) as pipe:
            pipe.zremrangebyscore(key, 0, window_start)
            pipe.zcard(key)
            pipe.zadd(key, {str(now): now})
            pipe.expire(key, self.window_seconds)
            results = await pipe.execute()

        request_count = results[1]

        if request_count >= self.max_requests:
            return JSONResponse(
                status_code=429,
                content={"detail": f"Rate limit exceeded. Max {self.max_requests} requests per {self.window_seconds}s."}
            )

        return await call_next(request)