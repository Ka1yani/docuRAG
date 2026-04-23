"""
PDF Processor
=============
Extracts text from PDF documents page-by-page using pypdf.
"""

from pypdf import PdfReader
from app.logger import logger
from app.services.documentProcessors.base_processor import BaseProcessor


class PdfProcessor(BaseProcessor):
    """Extracts text content from PDF files using pypdf."""

    def extract(self, file_path: str, file_name: str) -> list[tuple[int, str]]:
        logger.info(f"[PdfProcessor] Extracting text from: {file_name}")
        
        reader = PdfReader(file_path)
        extracted_data = []

        for page_num in range(len(reader.pages)):
            page = reader.pages[page_num]
            text_content = page.extract_text()
            if text_content and text_content.strip():
                extracted_data.append((page_num + 1, text_content))

        logger.info(f"[PdfProcessor] Extracted {len(extracted_data)} page(s) from {file_name}")
        return extracted_data
