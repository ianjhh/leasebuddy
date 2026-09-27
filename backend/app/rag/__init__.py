# This file makes backend/app/rag/ a Python package.

from llama_index.embeddings.ollama import OllamaEmbedding
from app.config import settings

embedding_model = OllamaEmbedding(
    model_name=settings.EMBEDDING_MODEL,
    base_url=settings.OLLAMA_BASE_URL,
)
