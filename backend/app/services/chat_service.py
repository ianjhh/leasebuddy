# backend/app/services/chat_service.py

import json
import hashlib
import logging
from typing import Dict, Any
from uuid import UUID
from app.api.dependencies import get_db, get_redis
from app.rag.agent import run_agent
from app.config import settings

logger = logging.getLogger(__name__)

async def generate_chat_response(lease_id: UUID, query: str, session_id: str) -> Dict[str, Any]:
    """Manages the full lifecycle of a user asking a question."""
    query_hash = hashlib.md5(query.encode()).hexdigest()
    cache_key = f"chat_cache:{lease_id}:{query_hash}"

    # Check cache
    async for redis_client in get_redis():
        cached_answer = await redis_client.get(cache_key)
        if cached_answer:
            logger.info("Cache hit for lease %s, query hash %s", lease_id, query_hash)
            return json.loads(cached_answer)
        break

    # Run the agent
    final_state = await run_agent(lease_id, query)

    response_data = {
        "answer": final_state.answer,
        "citations": [c.dict() for c in final_state.citations]
    }

    # Save to cache
    async for redis_client in get_redis():
        await redis_client.setex(cache_key, settings.CACHE_TTL_SECONDS, json.dumps(response_data))
        break

    return response_data
