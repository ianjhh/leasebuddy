# backend/app/rag/indexer.py

import logging
import uuid

from llama_index.core.node_parser import SentenceSplitter
from llama_index.embeddings.ollama import OllamaEmbedding
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.lease import LeaseChunk

logger = logging.getLogger(__name__)

embedding_model = OllamaEmbedding(
    model_name=settings.EMBEDDING_MODEL,
    base_url=settings.OLLAMA_BASE_URL,
)

async def index_document(
    lease_id: str,
    extracted_pages: list[dict],
    db: AsyncSession
) -> int:
    """
    Takes a list of extracted pages, chunks them, generates vector embeddings,
    and saves everything to the database. Returns the total number of chunks created.
    """
    logger.info("Indexing lease %s...", lease_id)

    splitter = SentenceSplitter(chunk_size=512, chunk_overlap=50)
    chunk_models: list[LeaseChunk] = []

    for page in extracted_pages:
        page_num = page["page_num"]
        text = page["text"]

        if not text.strip():
            continue

        text_chunks = splitter.split_text(text)

        for chunk_text in text_chunks:
            embedding: list[float] = await embedding_model.aget_text_embedding(chunk_text)

            chunk = LeaseChunk(
                id=uuid.uuid4(),
                document_id=uuid.UUID(lease_id),
                text_content=chunk_text,
                embedding=embedding,
                chunk_metadata={"page_number": page_num}
            )
            chunk_models.append(chunk)

    db.add_all(chunk_models)
    await db.commit()

    total = len(chunk_models)
    logger.info("Indexing complete! Saved %d chunks for lease %s.", total, lease_id)
    return total