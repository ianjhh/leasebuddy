import json
import boto3
import fitz
import os
import time
import psycopg2 
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

s3 = boto3.client('s3', endpoint_url=os.getenv('AWS_ENDPOINT_URL'))
textract = boto3.client('textract', endpoint_url=os.getenv('AWS_ENDPOINT_URL'))

def get_db_connection():
    return psycopg2.connect(
        dbname=os.getenv("DB_NAME", "leasebuddy"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "postgres"),
        host=os.getenv("DB_HOST", "host.docker.internal"),
        port=os.getenv("DB_PORT", "5432")
    )

def extract_text_from_pdf(file_path):
    doc = fitz.open(file_path)
    full_text = ""
    for page in doc:
        full_text += page.get_text() + "\n\n"
    return full_text, len(doc)

def extract_text_with_textract(bucket, key):
    response = textract.start_document_text_detection(
        DocumentLocation={'S3Object': {'Bucket': bucket, 'Name': key}}
    )
    job_id = response['JobId']
    
    while True:
        status_response = textract.get_document_text_detection(JobId=job_id)
        status = status_response['JobStatus']
        if status == 'SUCCEEDED':
            break
        elif status == 'FAILED':
            raise Exception("Textract failed to process document")
        
        logger.info("Waiting for Textract to finish...")
        time.sleep(2)
    
    extracted_text = ""
    for item in status_response['Blocks']:
        if item['BlockType'] == 'LINE':
            extracted_text += item['Text'] + "\n"
            
    return extracted_text, status_response['DocumentMetadata']['Pages']

def handler(event, context):
    logger.info("Extract Lambda started!")
    
    bucket = event['bucket']
    key = event['key']
    file_type = event['file_type']
    
    extracted_text = ""
    page_count = 0
    
    if file_type == 'text_pdf':
        download_path = f'/tmp/{os.path.basename(key)}'
        s3.download_file(bucket, key, download_path)
        extracted_text, page_count = extract_text_from_pdf(download_path)
        os.remove(download_path)
        
    elif file_type in ['scanned_pdf', 'image']:
        extracted_text, page_count = extract_text_with_textract(bucket, key)
        
    lease_id = os.path.basename(key).split('.')[0]
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    metadata_json = json.dumps({"page_count": page_count, "extracted_text": extracted_text})
    cur.execute("""
        INSERT INTO lease_documents (id, filename, metadata, status)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (id) DO UPDATE 
        SET metadata = EXCLUDED.metadata,
            status = EXCLUDED.status;
    """, (lease_id, os.path.basename(key), metadata_json, 'extracted'))
    
    conn.commit()
    cur.close()
    conn.close()
    
    return {
        'lease_id': lease_id,
        'bucket': bucket,
        'key': key,
        'status': 'extracted'
    }
