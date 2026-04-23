"""
OCR Backend Interface
=====================
Abstract base class and shared types for all OCR backends.
"""

from __future__ import annotations

import os
from abc import ABC, abstractmethod
from dataclasses import dataclass


# ── Type Aliases ────────────────────────────────────────────────────────────
ExtractionResult = list[tuple[int, str]]


@dataclass(frozen=True)
class OCRResponse:
    """Standardized response from any OCR backend."""
    text: str
    source: str
    inference_seconds: float = 0.0

    @property
    def is_empty(self) -> bool:
        return not self.text.strip()


class OCRBackend(ABC):
    """
    Abstract interface for an OCR extraction backend.

    Each backend must implement:
        - name:         Human-readable label for logging
        - is_available: Quick health/connectivity check
        - extract_text: Actual OCR inference
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable backend name for logs."""
        ...

    @abstractmethod
    def is_available(self) -> bool:
        """Returns True if this backend is ready to accept requests."""
        ...

    @abstractmethod
    def extract_text(self, file_path: str, file_name: str) -> OCRResponse:
        """
        Runs OCR on the given image file.

        Args:
            file_path: Absolute path to the image on disk.
            file_name: Original filename (for content-type detection).

        Returns:
            OCRResponse with extracted text (may be empty on failure).
        """
        ...


def mime_type(file_name: str) -> str:
    """Returns the MIME type for a given image filename."""
    ext = os.path.splitext(file_name.lower())[1]
    return {
        ".png":  "image/png",
        ".jpg":  "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
    }.get(ext, "application/octet-stream")
