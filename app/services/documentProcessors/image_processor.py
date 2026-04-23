"""
Image Processor (Docker OCR Client)
====================================
Extracts text from images by calling the dockerized DeepSeek-OCR-2 service.

All model loading, monkey patches, and inference logic has been moved to
the `docurag-ocr` Docker container. This processor is now a thin HTTP
client that sends the image and receives extracted text.

Architecture:
    ImageProcessor.extract()
         |
         | HTTP POST /ocr (multipart file upload)
         v
    docurag-ocr container (Python 3.10, DeepSeek-OCR-2)
         |
         | Returns JSON { text, characters, words, inference_time_seconds }
         v
    Returns [(1, formatted_text)]
"""

import os
import requests
from app.logger import logger
from app.services.documentProcessors.base_processor import BaseProcessor

# The OCR service URL -- configurable via environment variable.
# Default points to the Docker container running on localhost:5000.
OCR_SERVICE_URL = os.getenv("OCR_SERVICE_URL", "http://localhost:5000")


class ImageProcessor(BaseProcessor):
    """
    Extracts text from images by delegating to the DeepSeek-OCR-2 Docker service.
    
    The Docker service handles all model loading and inference in a clean
    Python 3.10 environment, eliminating all Windows/Python 3.14 compatibility issues.
    """

    def extract(self, file_path: str, file_name: str) -> list[tuple[int, str]]:
        logger.info(f"[ImageProcessor] Sending image to OCR service: {file_name}")
        
        # Check service health before sending heavy request
        if not self._check_health():
            logger.error("[ImageProcessor] OCR service is not available. Is the Docker container running?")
            logger.error(f"[ImageProcessor] Expected at: {OCR_SERVICE_URL}")
            logger.error("[ImageProcessor] Start it with: docker run -p 5000:5000 docurag-ocr")
            return []
        
        # Send image to the OCR Docker service
        try:
            with open(file_path, "rb") as f:
                response = requests.post(
                    f"{OCR_SERVICE_URL}/ocr",
                    files={"file": (file_name, f, self._get_mime_type(file_name))},
                    timeout=300,  # 5 minute timeout for large images / first model load
                )
            
            if response.status_code != 200:
                error_detail = response.json().get("detail", response.text)
                logger.error(f"[ImageProcessor] OCR service returned {response.status_code}: {error_detail}")
                return []
            
            data = response.json()
            extracted_text = data.get("text", "")
            inference_time = data.get("inference_time_seconds", 0)
            
            logger.info(f"[ImageProcessor] OCR service response received in {inference_time}s")
            
        except requests.ConnectionError:
            logger.error(f"[ImageProcessor] Cannot connect to OCR service at {OCR_SERVICE_URL}")
            logger.error("[ImageProcessor] Start the Docker container: docker run -p 5000:5000 docurag-ocr")
            return []
        except requests.Timeout:
            logger.error("[ImageProcessor] OCR service timed out (>300s). Image may be too large.")
            return []
        except Exception as e:
            logger.error(f"[ImageProcessor] Unexpected error calling OCR service: {e}")
            return []
        
        if not extracted_text.strip():
            logger.warning("[ImageProcessor] OCR service returned empty text -- no content detected.")
            return []
        
        # ── Log raw extraction ──────────────────────────────────────────
        logger.info("=" * 60)
        logger.info("[ImageProcessor] RAW EXTRACTION OUTPUT")
        logger.info(f"  Characters: {len(extracted_text)}")
        logger.info(f"  Words: {len(extracted_text.split())}")
        logger.info("-" * 60)
        for line_num, line in enumerate(extracted_text.splitlines(), 1):
            logger.info(f"  OCR Line {line_num:03d} | {line}")
        logger.info("=" * 60)
        
        # Apply semantic framing for the LLM contextual window
        formatted_text = f"[Transcribed Image Content (DeepSeek-OCR-2)]:\n{extracted_text}"
        return [(1, formatted_text)]

    def _check_health(self) -> bool:
        """Checks if the OCR Docker service is reachable and healthy."""
        try:
            resp = requests.get(f"{OCR_SERVICE_URL}/health", timeout=5)
            health = resp.json()
            if health.get("model_loaded"):
                logger.info("[ImageProcessor] OCR service is healthy (model loaded)")
                return True
            else:
                logger.warning(f"[ImageProcessor] OCR service unhealthy: {health}")
                return False
        except Exception:
            return False

    @staticmethod
    def _get_mime_type(file_name: str) -> str:
        """Returns the MIME type for a given image filename."""
        ext = os.path.splitext(file_name.lower())[1]
        mime_map = {
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".webp": "image/webp",
        }
        return mime_map.get(ext, "application/octet-stream")
