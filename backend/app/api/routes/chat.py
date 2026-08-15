# backend/app/api/routes/chat.py

import logging
import json
import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from uuid import UUID

from app.services.chat_service import generate_chat_response

logger = logging.getLogger(__name__)

router = APIRouter()

@router.websocket("/ws/chat/{lease_id}")
async def websocket_chat(websocket: WebSocket, lease_id: UUID) -> None:
    """WebSocket endpoint for real-time chat with a lease."""
    await websocket.accept()

    try:
        while True:
            raw_message = await websocket.receive_text()
            data = json.loads(raw_message)

            if data.get("type") == "query":
                user_query = data.get("content")
                session_id = data.get("session_id", "default")

                response = await generate_chat_response(lease_id, user_query, session_id)
                answer_text = response["answer"]

                words = answer_text.split(" ")
                for word in words:
                    await websocket.send_json({
                        "type": "token",
                        "content": word + " "
                    })
                    await asyncio.sleep(0.05)

                await websocket.send_json({
                    "type": "citations",
                    "data": response["citations"]
                })

                await websocket.send_json({"type": "done"})

    except WebSocketDisconnect:
        logger.info("Client disconnected from lease %s", lease_id)
    except Exception as e:
        logger.exception("WebSocket error for lease %s", lease_id)
        await websocket.send_json({
            "type": "error",
            "message": str(e)
        })
