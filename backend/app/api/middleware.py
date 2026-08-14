# backend/app/api/middleware.py

import time
import logging
from collections import defaultdict
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Logs every incoming request and how long it took to process."""
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        logger.info(f"Incoming Request: {request.method} {request.url.path}")
        
        response = await call_next(request)
        
        process_time = time.time() - start_time
        logger.info(f"Completed Request: {request.method} {request.url.path} in {process_time:.4f} secs")
        response.headers["X-Process-Time"] = str(process_time)
        return response

import redis.asyncio as redis
from app.config import settings

class SimpleRateLimitMiddleware(BaseHTTPMiddleware):
    """
    Sliding-window rate limiter using Redis.
    Allows at most `max_requests` requests per `window_seconds` per client IP.
    """
    def __init__(self, app, max_requests: int = 60, window_seconds: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        # Initialize a Redis connection pool for the middleware
        self.redis = redis.from_url(settings.REDIS_URL, encoding="utf-8", decode_responses=True)

    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host
        now = time.time()
        window_start = now - self.window_seconds
        key = f"rate_limit:{client_ip}"

        # Use a Redis transaction (pipeline) to ensure atomic operations
        async with self.redis.pipeline(transaction=True) as pipe:
            # 1. Remove old timestamps outside the window
            pipe.zremrangebyscore(key, 0, window_start)
            # 2. Count remaining timestamps in the window
            pipe.zcard(key)
            # 3. Add current timestamp
            pipe.zadd(key, {str(now): now})
            # 4. Set expiry so we don't leak memory for old IPs
            pipe.expire(key, self.window_seconds)
            
            # Execute all commands at once
            results = await pipe.execute()
        
        # results[1] is the output of zcard (the number of requests in the window)
        request_count = results[1]
        
        if request_count >= self.max_requests:
            return JSONResponse(
                status_code=429,
                content={"detail": f"Rate limit exceeded. Max {self.max_requests} requests per {self.window_seconds}s."}
            )

        return await call_next(request)