"""
DOC/DOCX Processor
==================
Extracts text from Word documents paragraph-by-paragraph using python-docx.
"""

from docx import Document as DocxDocument
from app.logger import logger
from app.services.documentProcessors.base_processor import BaseProcessor


class DocProcessor(BaseProcessor):
    """Extracts text content from .doc/.docx files using python-docx."""

    def extract(self, file_path: str, file_name: str) -> list[tuple[int, str]]:
        logger.info(f"[DocProcessor] Extracting text from: {file_name}")

        doc = DocxDocument(file_path)
        extracted_data = []

        # Using paragraph index as "page" since word wrapping is dynamic
        for i, para in enumerate(doc.paragraphs):
            if para.text.strip():
                extracted_data.append((i + 1, para.text))

        logger.info(f"[DocProcessor] Extracted {len(extracted_data)} paragraph(s) from {file_name}")
        return extracted_data
