"""
Audio Processor
===============
Transcribes audio files (MP3, WAV, M4A) into timestamped text segments
using Faster-Whisper ASR.
"""

from app.logger import logger
from app.services.documentProcessors.base_processor import BaseProcessor

try:
    from faster_whisper import WhisperModel
except ImportError:
    WhisperModel = None


def _format_timestamp(seconds: float) -> str:
    """Converts seconds to MM:SS format for audio segment labeling."""
    mins = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{mins:02d}:{secs:02d}"


class AudioProcessor(BaseProcessor):
    """Transcribes audio files into timestamped text segments using Faster-Whisper."""

    def extract(self, file_path: str, file_name: str) -> list[tuple[int, str]]:
        if WhisperModel is None:
            raise ImportError("faster-whisper is not installed. Unable to process audio.")

        logger.info(f"[AudioProcessor] Initializing Whisper for: {file_name}")

        # Use CPU by default. Set device="cuda" if running on a GPU.
        # compute_type="int8" reduces memory usage for CPU.
        model = WhisperModel("base", device="cpu", compute_type="int8")

        segments, info = model.transcribe(file_path, beam_size=5)
        logger.info(
            f"[AudioProcessor] Detected language '{info.language}' "
            f"with probability {info.language_probability}"
        )

        extracted_data = []
        for i, segment in enumerate(segments):
            start_str = _format_timestamp(segment.start)
            end_str = _format_timestamp(segment.end)
            text_val = segment.text.strip()

            # Format text explicitly to bias the LLM with audio flow context
            formatted_text = f"[Audio Segment {start_str} - {end_str}]: {text_val}"

            # Use segment ordinal as the logical page number
            extracted_data.append((i + 1, formatted_text))

        logger.info(f"[AudioProcessor] Transcribed {len(extracted_data)} segment(s) from {file_name}")
        return extracted_data
