# backend/app/services/document_processor.py

import logging
import fitz  # PyMuPDF
from typing import List, Dict

logger = logging.getLogger(__name__)

async def process_document(file_bytes: bytes, filename: str) -> List[Dict]:
    """
    Takes a file, determines if it needs OCR, and extracts the text page by page.
    Returns a list of dicts, one per page: [{"page_num": 1, "text": "..."}, ...]
    """
    extension = filename.split(".")[-1].lower() if "." in filename else ""
    extracted_pages = []

    if extension in ["jpg", "jpeg", "png", "tiff"]:
        raise NotImplementedError(
            "Image OCR via AWS Textract is not yet configured. "
            "Please upload a digitally-created PDF."
        )

    if extension == "pdf":
        logger.info("PDF detected. Analysing...")
        pdf_document = fitz.open(stream=file_bytes, filetype="pdf")

        first_page_text = pdf_document[0].get_text()
        if len(first_page_text.strip()) < 50:
            pdf_document.close()
            raise NotImplementedError(
                "This PDF appears to be scanned (no digital text layer found). "
                "AWS Textract OCR is not yet configured. "
                "Please upload a digitally-created PDF."
            )

        logger.info("Digital PDF detected. Extracting text from %d pages...", len(pdf_document))
        for page_num in range(len(pdf_document)):
            page = pdf_document[page_num]
            extracted_pages.append({
                "page_num": page_num + 1,  # 1-indexed so page numbers match the real document
                "text": page.get_text(),
            })

        pdf_document.close()
        return extracted_pages

    raise ValueError(f"Unsupported file extension: '{extension}'")
