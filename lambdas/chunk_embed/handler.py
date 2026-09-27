import os
import httpx
import psycopg2
import json
from llama_index.core.node_parser import SentenceSplitter
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def get_db_connection():
    return psycopg2.connect(
        dbname=os.environ["DB_NAME"],
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        host=os.environ["DB_HOST"],
        port=os.getenv("DB_PORT", "5432")
    )

def get_embedding(text):
    ollama_host = os.environ["OLLAMA_HOST"]
    model_name = os.getenv("EMBEDDING_MODEL", "nomic-embed-text")
    response = httpx.post(f"{ollama_host}/api/embeddings", json={
        "model": model_name,
        "prompt": text
    }, timeout=120.0)
    response.raise_for_status()
    return response.json()['embedding']

def handler(event, context):
    logger.info("Chunk & Embed Lambda started!")
    lease_id = event['lease_id']
    
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT metadata FROM lease_documents WHERE id = %s", (lease_id,))
    result = cur.fetchone()
    
    if not result:
        raise Exception(f"Lease {lease_id} not found in database!")
        
    metadata = result[0]
    full_text = metadata.get("extracted_text", "")
    page_count = metadata.get("page_count", 1)
    
    splitter = SentenceSplitter(chunk_size=512, chunk_overlap=50)
    chunks = splitter.split_text(full_text)
    
    # Estimate page number for each chunk based on position in the full text
    chars_per_page = max(len(full_text) // page_count, 1) if page_count > 0 else len(full_text)
    
    for i, chunk_text in enumerate(chunks):
        logger.info("Generating embedding for chunk %d/%d", i+1, len(chunks))
        embedding = get_embedding(chunk_text)
        
        # Estimate page number from the chunk's approximate position
        chunk_start = full_text.find(chunk_text)
        estimated_page = (chunk_start // chars_per_page) + 1 if chunk_start >= 0 else 1
        estimated_page = min(estimated_page, page_count)
        
        chunk_meta = json.dumps({"page_number": estimated_page, "chunk_index": i})
        cur.execute("""
            INSERT INTO lease_chunks (document_id, text_content, embedding, chunk_metadata)
            VALUES (%s, %s, %s::vector, %s)
        """, (lease_id, chunk_text, embedding, chunk_meta))
    
    cur.execute("UPDATE lease_documents SET status = 'completed' WHERE id = %s", (lease_id,))
    conn.commit()
    cur.close()
    conn.close()
    
    return {
        'status': 'success',
        'lease_id': lease_id,
        'chunks_created': len(chunks)
    }
