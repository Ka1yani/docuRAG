"""
Docker OCR Backend
==================
Calls the dockerized DeepSeek-OCR-2 FastAPI service at localhost:5000.
"""

from __future__ import annotations

import os

import requests

from app.logger import logger
from app.services.documentProcessors.ocr_backends.base import OCRBackend, OCRResponse, mime_type

# ── Configuration ───────────────────────────────────────────────────────────
DOCKER_OCR_URL = os.getenv("OCR_SERVICE_URL", "http://localhost:5000")
HEALTH_CHECK_TIMEOUT = 5       # seconds
INFERENCE_TIMEOUT    = 300     # 5 minutes


class DockerOCRBackend(OCRBackend):
    """Calls the dockerized DeepSeek-OCR-2 FastAPI service."""

    def __init__(self, base_url: str = DOCKER_OCR_URL):
        self._base_url = base_url

    @property
    def name(self) -> str:
        return "Docker/DeepSeek-OCR-2"

    def is_available(self) -> bool:
        try:
            resp = requests.get(
                f"{self._base_url}/health",
                timeout=HEALTH_CHECK_TIMEOUT,
            )
            return resp.json().get("model_loaded", False)
        except Exception:
            return False

    def extract_text(self, file_path: str, file_name: str) -> OCRResponse:
        try:
            with open(file_path, "rb") as f:
                response = requests.post(
                    f"{self._base_url}/ocr",
                    files={"file": (file_name, f, mime_type(file_name))},
                    timeout=INFERENCE_TIMEOUT,
                )

            if response.status_code != 200:
                detail = response.json().get("detail", response.text)
                logger.error(f"[{self.name}] HTTP {response.status_code}: {detail}")
                return OCRResponse(text="", source=self.name)

            data = response.json()
            return OCRResponse(
                text=data.get("text", ""),
                source=self.name,
                inference_seconds=data.get("inference_time_seconds", 0),
            )

        except requests.Timeout:
            logger.error(f"[{self.name}] Timed out (>{INFERENCE_TIMEOUT}s)")
        except Exception as e:
            logger.error(f"[{self.name}] Request failed: {e}")

        return OCRResponse(text="", source=self.name)
