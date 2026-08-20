import os
import requests
import psycopg2
import json
from llama_index.core.node_parser import SentenceSplitter
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def get_db_connection():
    return psycopg2.connect(
        dbname=os.getenv("DB_NAME", "leasebuddy"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "postgres"),
        host=os.getenv("DB_HOST", "host.docker.internal"),
        port=os.getenv("DB_PORT", "5432")
    )

def get_embedding(text):
    ollama_host = os.getenv("OLLAMA_HOST", "http://host.docker.internal:11434")
    model_name = os.getenv("EMBEDDING_MODEL", "nomic-embed-text")
    response = requests.post(f"{ollama_host}/api/embeddings", json={
        "model": model_name,
        "prompt": text
    })
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
    
    splitter = SentenceSplitter(chunk_size=512, chunk_overlap=50)
    chunks = splitter.split_text(full_text)
    
    for i, chunk_text in enumerate(chunks):
        logger.info("Generating embedding for chunk %d/%d", i+1, len(chunks))
        embedding = get_embedding(chunk_text)
        
        chunk_meta = json.dumps({"page_number": 1, "chunk_index": i})
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
