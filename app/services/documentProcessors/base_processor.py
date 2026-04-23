"""
Base Processor Interface
========================
Abstract base class that all document processors must implement.
Enforces Liskov Substitution -- any processor can be swapped transparently.
"""

from abc import ABC, abstractmethod
from app.logger import logger


class BaseProcessor(ABC):
    """
    Abstract interface for document text extraction.

    Every concrete processor must implement `extract()` which returns
    a list of (page_number, text_content) tuples. The orchestrator
    handles chunking, embedding, and database storage uniformly.
    """

    @abstractmethod
    def extract(self, file_path: str, file_name: str) -> list[tuple[int, str]]:
        """
        Extract text content from a document file.

        Args:
            file_path: Absolute path to the uploaded file on disk.
            file_name: Original filename (used for logging context).

        Returns:
            List of (page_number, text_content) tuples.
            page_number is 1-indexed. For single-page formats (images, txt),
            return [(1, text)]. For multi-page formats, return one tuple per page.
            Empty list if no text could be extracted.
        """
        ...
