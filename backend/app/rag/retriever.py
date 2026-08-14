# backend/app/rag/retriever.py

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from llama_index.embeddings.ollama import OllamaEmbedding
from app.config import settings
from typing import List, Dict

embedding_model = OllamaEmbedding(
    model_name=settings.EMBEDDING_MODEL,
    base_url=settings.OLLAMA_BASE_URL,
)

async def hybrid_search(
    db: AsyncSession,
    lease_id: str,
    query_text: str,
    limit: int = 5
) -> List[Dict]:
    """
    Performs a hybrid search combining semantic (vector) and keyword (full-text) search,
    merged using Reciprocal Rank Fusion (RRF).
    """
    query_embedding: List[float] = await embedding_model.aget_text_embedding(query_text)
    query_embedding_str = "[" + ",".join(str(x) for x in query_embedding) + "]"
    
    rrf_query = text("""
    WITH
    semantic_search AS (
        SELECT
            lc.id,
            lc.text_content,
            (lc.chunk_metadata->>'page_number')::int AS page_number,
            ROW_NUMBER() OVER (ORDER BY lc.embedding <=> CAST(:query_embedding AS vector)) AS rank
        FROM lease_chunks lc
        WHERE lc.document_id = CAST(:lease_id AS uuid)
        LIMIT :candidate_limit
    ),
    keyword_search AS (
        SELECT
            lc.id,
            lc.text_content,
            (lc.chunk_metadata->>'page_number')::int AS page_number,
            ROW_NUMBER() OVER (
                ORDER BY ts_rank(
                    to_tsvector('english', lc.text_content),
                    plainto_tsquery('english', :query_text)
                ) DESC
            ) AS rank
        FROM lease_chunks lc
        WHERE lc.document_id = CAST(:lease_id AS uuid)
          AND to_tsvector('english', lc.text_content) @@ plainto_tsquery('english', :query_text)
        LIMIT :candidate_limit
    ),
    rrf_scores AS (
        SELECT
            COALESCE(s.id, k.id)                                          AS chunk_id,
            COALESCE(s.text_content, k.text_content)                      AS text_content,
            COALESCE(s.page_number, k.page_number)                        AS page_number,
            COALESCE(1.0 / (60.0 + s.rank), 0.0)
                + COALESCE(1.0 / (60.0 + k.rank), 0.0)                   AS rrf_score
        FROM semantic_search s
        FULL OUTER JOIN keyword_search k ON s.id = k.id
    )
    SELECT chunk_id, text_content, page_number, rrf_score
    FROM rrf_scores
    ORDER BY rrf_score DESC
    LIMIT :limit;
    """)
    
    result = await db.execute(
        rrf_query,
        {
            "query_embedding": query_embedding_str,
            "query_text": query_text,
            "lease_id": str(lease_id),
            "candidate_limit": limit * 10,
            "limit": limit,
        }
    )
    
    rows = result.fetchall()
    
    return [
        {
            "id": str(row.chunk_id),
            "text": row.text_content,
            "page": row.page_number,
            "score": float(row.rrf_score),
        }
        for row in rows
    ]