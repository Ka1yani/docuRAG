"""
Text Processor
==============
Reads plain text files (.txt) directly.
"""

from app.logger import logger
from app.services.documentProcessors.base_processor import BaseProcessor


class TextProcessor(BaseProcessor):
    """Reads raw text from .txt files."""

    def extract(self, file_path: str, file_name: str) -> list[tuple[int, str]]:
        logger.info(f"[TextProcessor] Reading plain text from: {file_name}")

        with open(file_path, "r", encoding="utf-8") as f:
            text_content = f.read()

        if text_content.strip():
            return [(1, text_content)]

        logger.warning(f"[TextProcessor] File is empty: {file_name}")
        return []
