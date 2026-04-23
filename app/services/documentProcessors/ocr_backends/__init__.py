"""
OCR Backends Package
====================
Pluggable OCR backend implementations for the ImageProcessor.

Exports:
    - OCRBackend:        Abstract interface
    - OCRResponse:       Standardized response dataclass
    - ExtractionResult:  Type alias
    - DockerOCRBackend:  Docker service client
    - OllamaOCRBackend:  Ollama vision API client
    - mime_type:         Image MIME type helper
"""

from app.services.documentProcessors.ocr_backends.base import (
    ExtractionResult,
    OCRBackend,
    OCRResponse,
    mime_type,
)
from app.services.documentProcessors.ocr_backends.docker_backend import DockerOCRBackend
from app.services.documentProcessors.ocr_backends.ollama_backend import OllamaOCRBackend

__all__ = [
    "ExtractionResult",
    "OCRBackend",
    "OCRResponse",
    "DockerOCRBackend",
    "OllamaOCRBackend",
    "mime_type",
]
