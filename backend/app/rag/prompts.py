# backend/app/rag/prompts.py

from typing import List, Dict
import httpx
from app.config import settings

QA_SYSTEM_PROMPT = """\
You are a highly accurate legal assistant specialising in residential and \
commercial leases. Your job is to answer the user's question using ONLY the \
context provided below.

Context blocks (excerpts from the lease) are provided with their page numbers.

RULES:
1. Do not use outside knowledge. If the answer is not in the context, say \
"I cannot find the answer to that in the provided lease document."
2. Always cite your sources using the page number in the context. \
Format citations like this: [Page 4].
3. Be concise but thorough.
4. If there are conflicting statements in the lease, point them out.

CONTEXT:
{context_string}
"""


def build_context_string(retrieved_chunks: List[Dict]) -> str:
    """
    Formats retrieved database chunks into a single readable block of text
    that the LLM can easily parse.
    """
    lines = []
    for chunk in retrieved_chunks:
        lines.append(f"---")
        lines.append(f"[Page {chunk['page']}]")
        lines.append(chunk['text'].strip())
    return "\n".join(lines)


async def ask_ollama(system_prompt: str, user_question: str) -> str:
    """
    Sends the filled system prompt and the user's question to the local
    Ollama server and returns the model's reply.
    """
    payload = {
        "model": settings.LLM_MODEL,
        "stream": False,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_question},
        ],
    }
    
    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            f"{settings.OLLAMA_BASE_URL}/api/chat",
            json=payload,
        )
        response.raise_for_status()
        data = response.json()
    
    return data["message"]["content"]


async def answer_question(
    user_question: str,
    retrieved_chunks: List[Dict]
) -> str:
    """
    High-level function that ties everything together:
    1. Formats the retrieved chunks into a context string.
    2. Fills the system prompt with that context.
    3. Sends the prompt + question to Ollama.
    4. Returns the model's answer.
    """
    context_string  = build_context_string(retrieved_chunks)
    system_prompt   = QA_SYSTEM_PROMPT.format(context_string=context_string)
    answer          = await ask_ollama(system_prompt, user_question)
    return answer