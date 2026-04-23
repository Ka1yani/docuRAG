"""
DocuRAG OCR Microservice
========================
Isolated Docker service running DeepSeek-OCR-2 on Python 3.10.

Uses Dogacel/Universal-DeepSeek-OCR-2 -- a community fork that removes
all hardcoded .cuda() calls from the original DeepSeek-OCR-2, enabling
native CPU/MPS inference WITHOUT any monkey patches.

Architecture:
    DocuRAG Backend (Python 3.14, Windows)
         |
         | HTTP POST /ocr (multipart image)
         v
    This Container (Python 3.10, Linux)
         |
         | Universal-DeepSeek-OCR-2 model.infer()
         v
    Returns extracted text as JSON

API:
    POST /ocr        - Extract text from an uploaded image
    GET  /health      - Health check (returns model load status)
"""

import os
import sys
import time
import shutil
import tempfile
import torch
from contextlib import asynccontextmanager
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse


# ── Application State ───────────────────────────────────────────────────────
_model = None
_tokenizer = None
_model_loaded = False
_load_error = None


def _load_model():
    """
    Loads the Universal-DeepSeek-OCR-2 model into memory.
    
    Uses Dogacel/Universal-DeepSeek-OCR-2 which has all .cuda() calls
    removed from the inference code, so it works natively on CPU
    without any monkey patches.
    """
    global _model, _tokenizer, _model_loaded, _load_error

    if _model_loaded:
        return

    try:
        from transformers import AutoModel, AutoTokenizer

        # Key difference: Dogacel's fork, NOT deepseek-ai/DeepSeek-OCR-2
        model_name = "Dogacel/Universal-DeepSeek-OCR-2"

        print("=" * 60)
        print(f"Loading {model_name} (CPU / float16)...")
        print("This may take a few minutes on first run (downloading weights).")
        print("=" * 60)

        start = time.time()

        _tokenizer = AutoTokenizer.from_pretrained(
            model_name,
            trust_remote_code=True
        )

        _model = AutoModel.from_pretrained(
            model_name,
            trust_remote_code=True,
            use_safetensors=True
        )
        # float16 matches what Dogacel's sample_cpu.py uses
        _model = _model.eval().to("cpu").to(torch.float16)

        elapsed = time.time() - start
        print(f"Model loaded successfully in {elapsed:.1f}s")
        _model_loaded = True

    except Exception as e:
        _load_error = str(e)
        print(f"FATAL: Failed to load model: {e}", file=sys.stderr)
        raise


# ── FastAPI Lifespan (modern pattern, no deprecation warning) ───────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load model on startup, cleanup on shutdown."""
    _load_model()
    yield


app = FastAPI(
    title="DocuRAG OCR Service",
    version="2.0.0",
    lifespan=lifespan
)


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy" if _model_loaded else "unhealthy",
        "model_loaded": _model_loaded,
        "model": "Dogacel/Universal-DeepSeek-OCR-2",
        "error": _load_error,
        "device": "cpu",
        "dtype": "float16",
    }


@app.post("/ocr")
async def ocr(file: UploadFile = File(...)):
    """
    Extract text from an uploaded image using Universal-DeepSeek-OCR-2.

    Accepts: multipart/form-data with 'file' field (PNG, JPG, JPEG, WEBP).
    Returns: JSON with extracted text, character count, and word count.
    """
    if not _model_loaded:
        raise HTTPException(status_code=503, detail="Model not loaded yet.")

    # Validate file type
    allowed = {".png", ".jpg", ".jpeg", ".webp"}
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {ext}. Allowed: {allowed}"
        )

    # Save to temp file (model.infer() needs a file path)
    tmp_dir = tempfile.mkdtemp()
    tmp_path = os.path.join(tmp_dir, file.filename or "upload.png")

    try:
        with open(tmp_path, "wb") as f:
            content = await file.read()
            f.write(content)

        # Run inference with structured grounding prompt
        prompt = "<image>\n<|grounding|>Convert the document to markdown."

        print(f"[OCR] Processing: {file.filename} ({len(content)} bytes)")
        start = time.time()

        extracted_text = _run_inference(tmp_path, prompt)

        # Fallback to simpler prompt if grounding fails
        if not extracted_text.strip():
            print("[OCR] Grounding prompt returned empty, trying Free OCR...")
            extracted_text = _run_inference(tmp_path, "<image>\nFree OCR.")

        elapsed = time.time() - start
        print(f"[OCR] Done in {elapsed:.1f}s - {len(extracted_text)} chars extracted")

        return JSONResponse(content={
            "text": extracted_text,
            "characters": len(extracted_text),
            "words": len(extracted_text.split()) if extracted_text.strip() else 0,
            "inference_time_seconds": round(elapsed, 2),
        })

    except Exception as e:
        print(f"[OCR] Error: {e}", file=sys.stderr)
        raise HTTPException(status_code=500, detail=f"OCR extraction failed: {str(e)}")

    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


def _run_inference(image_path: str, prompt: str) -> str:
    """Runs Universal-DeepSeek-OCR-2 inference on a single image."""
    output_dir = os.path.dirname(image_path)

    try:
        result = _model.infer(
            _tokenizer,
            prompt=prompt,
            image_file=image_path,
            output_path=output_dir,
            base_size=1024,
            image_size=768,
            crop_mode=True,
            save_results=False,
            eval_mode=True,
        )
        return result if isinstance(result, str) else str(result)
    except Exception as e:
        print(f"[OCR] Inference error: {e}")
        return ""


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
