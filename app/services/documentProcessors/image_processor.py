"""
Image Processor -- Multi-Backend OCR with Automatic Failover
=============================================================

Lightweight orchestrator that tries OCR backends in priority order:

    1. Docker OCR service  (full DeepSeek-OCR-2, high fidelity)
    2. Ollama deepseek-ocr (3B quantized, lightweight fallback)

To add a new backend, create a class implementing OCRBackend
and append it to self._backends (Open/Closed Principle).
"""

from __future__ import annotations

from app.logger import logger
from app.services.documentProcessors.base_processor import BaseProcessor
from app.services.documentProcessors.ocr_backends import (
    ExtractionResult,
    OCRBackend,
    OCRResponse,
    DockerOCRBackend,
    OllamaOCRBackend,
)


class ImageProcessor(BaseProcessor):
    """
    Extracts text from images using a prioritized chain of OCR backends.

    Backends are tried in order. The first one that is available AND
    returns non-empty text wins.
    """

    def __init__(self):
        self._backends: list[OCRBackend] = [
            DockerOCRBackend(),
            OllamaOCRBackend(),
        ]

    def extract(self, file_path: str, file_name: str) -> ExtractionResult:
        logger.info(f"[ImageProcessor] Processing: {file_name}")

        for backend in self._backends:
            if not backend.is_available():
                logger.info(f"[ImageProcessor] {backend.name} is not available, skipping")
                continue

            logger.info(f"[ImageProcessor] Using {backend.name}")
            result = backend.extract_text(file_path, file_name)

            if not result.is_empty:
                return self._format_output(result)

            logger.warning(f"[ImageProcessor] {backend.name} returned empty text")

        logger.error("[ImageProcessor] All OCR backends failed -- no text extracted")
        return []

    @staticmethod
    def _format_output(result: OCRResponse) -> ExtractionResult:
        """Logs the raw extraction and wraps it for the chunking pipeline."""
        text = result.text

        logger.info("=" * 60)
        logger.info(f"[ImageProcessor] RAW EXTRACTION ({result.source})")
        logger.info(f"  Characters: {len(text)}  |  Words: {len(text.split())}")
        if result.inference_seconds:
            logger.info(f"  Inference:  {result.inference_seconds}s")
        logger.info("-" * 60)
        for num, line in enumerate(text.splitlines(), 1):
            logger.info(f"  OCR Line {num:03d} | {line}")
        logger.info("=" * 60)

        formatted = f"[Transcribed Image Content ({result.source})]:\n{text}"
        return [(1, formatted)]
