import json               
import urllib.parse       
import boto3              
import fitz               
import os                 
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Create a client to talk to S3 (Amazon's file storage)
# We use endpoint_url so it can talk to LocalStack when testing locally
s3 = boto3.client('s3', endpoint_url=os.getenv('AWS_ENDPOINT_URL'))

def handler(event, context):
    logger.info("Classify Lambda started!")
    
    bucket = event['detail']['bucket']['name']
    key = urllib.parse.unquote_plus(event['detail']['object']['key'])
    
    download_path = f'/tmp/{os.path.basename(key)}'
    logger.info("Downloading %s from bucket %s to %s", key, bucket, download_path)
    
    s3.download_file(bucket, key, download_path)
    
    file_type = "unknown"
    
    if key.lower().endswith(('.png', '.jpg', '.jpeg')):
        file_type = 'image'
    elif key.lower().endswith('.pdf'):
        doc = fitz.open(download_path)
        has_text = False
        
        for page_num in range(min(3, len(doc))):
            page = doc.load_page(page_num)
            text = page.get_text()
            if len(text.strip()) > 50:
                has_text = True
                break
                
        if has_text:
            file_type = 'text_pdf'
        else:
            file_type = 'scanned_pdf'
            
        doc.close()
    
    os.remove(download_path)
    
    return {
        'statusCode': 200,
        'bucket': bucket,
        'key': key,
        'file_type': file_type
    }
