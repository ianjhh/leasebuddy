# backend/app/api/routes/chat.py

import json
import logging
from uuid import UUID

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from llama_index.llms.ollama import Ollama

from app.config import settings
from app.rag.agent import run_agent
from app.rag.prompts import QA_SYSTEM_PROMPT, build_context_string

logger = logging.getLogger(__name__)

router = APIRouter()

llm = Ollama(
    model=settings.LLM_MODEL,
    base_url=settings.OLLAMA_BASE_URL,
    request_timeout=120.0,
    context_window=4096,
    additional_kwargs={"num_ctx": 4096},
)


@router.websocket("/ws/chat/{lease_id}")
async def websocket_chat(websocket: WebSocket, lease_id: UUID) -> None:
    """WebSocket endpoint for real-time chat with a lease using true LLM token streaming."""
    await websocket.accept()

    try:
        while True:
            raw_message = await websocket.receive_text()
            data = json.loads(raw_message)

            if data.get("type") == "query":
                user_query = data.get("content")

                # Run the agent to get retrieval + relevance checking
                final_state = await run_agent(lease_id, user_query)

                # Build context from retrieved chunks
                chunks_as_dicts = [
                    {"page": c.page, "text": c.text}
                    for c in final_state.retrieved_chunks
                ]
                context_string = build_context_string(chunks_as_dicts)
                system_prompt = QA_SYSTEM_PROMPT.format(context_string=context_string)

                # Stream tokens directly from the LLM
                prompt = f"{system_prompt}\n\nQuestion: {user_query}"
                async for token_response in await llm.astream_complete(prompt):
                    await websocket.send_json({
                        "type": "token",
                        "content": token_response.delta,
                    })

                # Send citations after streaming completes
                await websocket.send_json({
                    "type": "citations",
                    "data": [
                        {"page_num": c.page, "snippet": c.text}
                        for c in final_state.retrieved_chunks
                    ],
                })

                await websocket.send_json({"type": "done"})

    except WebSocketDisconnect:
        logger.info("Client disconnected from lease %s", lease_id)
    except Exception:
        logger.exception("WebSocket error for lease %s", lease_id)
        await websocket.send_json({
            "type": "error",
            "message": "An internal error occurred. Please try again.",
        })
