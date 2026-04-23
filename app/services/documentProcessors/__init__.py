"""
Document Processors Package
============================
SOLID-compliant processor registry for multi-format document extraction.

Each processor implements the BaseProcessor interface and is registered
in the PROCESSOR_REGISTRY, which maps file extensions to their handler.
Adding a new format requires only creating a new processor class and
registering it here -- no existing code needs modification (Open/Closed).
"""

from app.services.documentProcessors.base_processor import BaseProcessor
from app.services.documentProcessors.pdf_processor import PdfProcessor
from app.services.documentProcessors.doc_processor import DocProcessor
from app.services.documentProcessors.audio_processor import AudioProcessor
from app.services.documentProcessors.image_processor import ImageProcessor
from app.services.documentProcessors.text_processor import TextProcessor

# ── Processor Registry ─────────────────────────────────────────────────────
# Maps file extensions to their responsible processor class.
# To add a new format, create a processor and register it here.
PROCESSOR_REGISTRY: dict[str, BaseProcessor] = {
    ".pdf":  PdfProcessor(),
    ".doc":  DocProcessor(),
    ".docx": DocProcessor(),
    ".mp3":  AudioProcessor(),
    ".wav":  AudioProcessor(),
    ".m4a":  AudioProcessor(),
    ".png":  ImageProcessor(),
    ".jpg":  ImageProcessor(),
    ".jpeg": ImageProcessor(),
    ".webp": ImageProcessor(),
    ".txt":  TextProcessor(),
}


def get_processor(extension: str) -> BaseProcessor:
    """
    Factory function that returns the appropriate processor for a file extension.

    Args:
        extension: Lowercase file extension including dot (e.g. ".pdf").

    Returns:
        BaseProcessor instance capable of extracting text from that format.

    Raises:
        ValueError: If no processor is registered for the given extension.
    """
    processor = PROCESSOR_REGISTRY.get(extension)
    if processor is None:
        raise ValueError(
            f"Unsupported file extension: {extension}. "
            f"Registered formats: {', '.join(sorted(PROCESSOR_REGISTRY.keys()))}"
        )
    return processor
