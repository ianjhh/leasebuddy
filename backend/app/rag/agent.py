# backend/app/rag/agent.py

import json
from typing import Optional, List, Dict, Any, AsyncGenerator
from uuid import UUID
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, END
from llama_index.core.llms import ChatMessage, MessageRole
from llama_index.llms.ollama import Ollama

from app.rag.retriever import hybrid_search
from app.config import settings
from app.api.dependencies import get_db

class ChunkResult(BaseModel):
    id: str
    text: str
    page: int
    score: float

class Citation(BaseModel):
    page_num: int
    snippet: str

class QAState(BaseModel):
    lease_id: UUID
    query: str
    query_analysis: Optional[Dict[str, Any]] = None
    retrieved_chunks: List[ChunkResult] = Field(default_factory=list)
    relevance_score: Optional[float] = None
    answer: Optional[str] = None
    citations: List[Citation] = Field(default_factory=list)
    retry_count: int = 0
    error: Optional[str] = None

llm = Ollama(model=settings.LLM_MODEL, base_url=settings.OLLAMA_BASE_URL, request_timeout=120.0)

async def analyze_query(state: QAState) -> QAState:
    prompt = f"""
    Analyze the following query about a lease agreement.
    Extract the main entities and keywords for searching.
    Return ONLY valid JSON with a 'keywords' list.
    Query: {state.query}
    """
    response = await llm.acomplete(prompt)
    try:
        analysis = json.loads(response.text)
        state.query_analysis = analysis
    except:
        state.query_analysis = {"keywords": [state.query]}
    return state

async def retrieve_context(state: QAState) -> QAState:
    keywords = state.query_analysis.get("keywords", [state.query])
    search_term = " ".join(keywords)
    async for db_session in get_db():
        raw_chunks = await hybrid_search(db_session, state.lease_id, search_term, limit=5)
        break
    state.retrieved_chunks = [ChunkResult(**c) for c in raw_chunks]
    state.retry_count += 1
    return state

async def check_relevance(state: QAState) -> QAState:
    context_str = "\n".join([c.text for c in state.retrieved_chunks])
    prompt = f"""
    Given the user's question and the retrieved lease context, rate how relevant
    the context is for answering the question on a scale of 0.0 to 1.0.
    Return ONLY a number.
    Question: {state.query}
    Context: {context_str}
    """
    response = await llm.acomplete(prompt)
    try:
        score = float(response.text.strip())
        state.relevance_score = score
    except:
        state.relevance_score = 1.0
    return state

async def generate_answer(state: QAState) -> QAState:
    context_str = ""
    for idx, chunk in enumerate(state.retrieved_chunks):
        context_str += f"[Page {chunk.page}] {chunk.text}\n"
    prompt = f"""
    You are a helpful real estate assistant. Answer the user's question using ONLY
    the provided context from their lease agreement.
    Whenever you state a fact, cite the page number like this: (Page X).
    If the context does not contain the answer, say "I cannot find this in the lease."

    Context:
    {context_str}

    Question: {state.query}
    """
    response = await llm.acomplete(prompt)
    state.answer = response.text
    return state

async def format_citations(state: QAState) -> QAState:
    state.citations = [
        Citation(page_num=c.page, snippet=c.text)
        for c in state.retrieved_chunks
    ]
    return state

def should_retry(state: QAState) -> str:
    if state.relevance_score < 0.5 and state.retry_count < 2:
        return "retrieve_context"
    return "generate_answer"

workflow = StateGraph(QAState)
workflow.add_node("analyze_query", analyze_query)
workflow.add_node("retrieve_context", retrieve_context)
workflow.add_node("check_relevance", check_relevance)
workflow.add_node("generate_answer", generate_answer)
workflow.add_node("format_citations", format_citations)

workflow.set_entry_point("analyze_query")
workflow.add_edge("analyze_query", "retrieve_context")
workflow.add_edge("retrieve_context", "check_relevance")
workflow.add_conditional_edges(
    "check_relevance",
    should_retry,
    {
        "retrieve_context": "retrieve_context",
        "generate_answer": "generate_answer"
    }
)
workflow.add_edge("generate_answer", "format_citations")
workflow.add_edge("format_citations", END)

app = workflow.compile()

async def run_agent(lease_id: UUID, query: str) -> QAState:
    initial_state = QAState(lease_id=lease_id, query=query)
    final_dict = await app.ainvoke(initial_state.dict())
    return QAState(**final_dict)
