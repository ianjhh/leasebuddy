# backend/app/services/document_processor.py

import asyncio
import logging

import fitz  # PyMuPDF

logger = logging.getLogger(__name__)


def _extract_pdf_pages(file_bytes: bytes) -> list[dict]:
    """Synchronous PDF text extraction — runs in a thread pool."""
    pdf_document = fitz.open(stream=file_bytes, filetype="pdf")

    first_page_text = pdf_document[0].get_text()
    if len(first_page_text.strip()) < 50:
        pdf_document.close()
        raise NotImplementedError(
            "This PDF appears to be scanned (no digital text layer found). "
            "AWS Textract OCR is not yet configured. "
            "Please upload a digitally-created PDF."
        )

    extracted_pages = []
    for page_num in range(len(pdf_document)):
        page = pdf_document[page_num]
        extracted_pages.append({
            "page_num": page_num + 1,
            "text": page.get_text(),
        })

    pdf_document.close()
    return extracted_pages


async def process_document(file_bytes: bytes, filename: str) -> list[dict]:
    """
    Takes a file, determines if it needs OCR, and extracts the text page by page.
    Returns a list of dicts, one per page: [{"page_num": 1, "text": "..."}, ...]
    """
    extension = filename.split(".")[-1].lower() if "." in filename else ""

    if extension in ["jpg", "jpeg", "png", "tiff"]:
        raise NotImplementedError(
            "Image OCR via AWS Textract is not yet configured. "
            "Please upload a digitally-created PDF."
        )

    if extension == "pdf":
        logger.info("PDF detected. Offloading extraction to thread pool...")
        return await asyncio.to_thread(_extract_pdf_pages, file_bytes)

    raise ValueError(f"Unsupported file extension: '{extension}'")
