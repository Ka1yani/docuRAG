"""
Document Processing Orchestrator
=================================
Thin orchestrator that delegates extraction to the appropriate processor
via the processor registry, then handles chunking, embedding, and DB storage.

This module is the ONLY entry point for document ingestion. It follows the
Dependency Inversion principle -- it depends on the BaseProcessor abstraction,
not on any concrete processor implementation.
"""

import os
from sqlalchemy.orm import Session
from app.models import Document, DocumentChunk
from app.services.llm_service import get_embedding
from app.services.documentProcessors import get_processor
from app.logger import logger


def chunk_text(text_content: str, word_chunk_size: int = 400) -> list[str]:
    """Splits text into word-level chunks for embedding storage."""
    words = text_content.split()
    chunks = []
    for i in range(0, len(words), word_chunk_size):
        chunk = " ".join(words[i : i + word_chunk_size])
        if chunk.strip():
            chunks.append(chunk)
    return chunks


def process_and_store_document(file_path: str, file_name: str, db: Session):
    """
    Main document ingestion pipeline.

    1. Creates a Document record in the database.
    2. Delegates text extraction to the appropriate processor (PDF, audio, image, etc).
    3. Chunks the extracted text, generates vector embeddings, and stores them in DuckDB.

    Args:
        file_path: Absolute path to the uploaded file on disk.
        file_name: Original filename from the upload.
        db: SQLAlchemy database session.

    Returns:
        Document: The created database record with all chunks attached.

    Raises:
        ValueError: If the file extension is not supported.
    """
    # 1. Create Document record
    db_doc = Document(file_name=file_name)
    db.add(db_doc)
    db.commit()
    db.refresh(db_doc)

    _, ext = os.path.splitext(file_name.lower())
    logger.info(f"Extracting {ext} logic for {file_name}")

    # 2. Delegate extraction to the appropriate processor
    processor = get_processor(ext)
    extracted_data = processor.extract(file_path, file_name)

    # 3. Chunk and Store
    total_chunks = 0
    for page_num, text_content in extracted_data:
        # Clean text
        clean_text = " ".join(text_content.replace("\\n", " ").split())
        if not clean_text:
            continue

        chunks = chunk_text(clean_text)

        # ── Log chunks before DuckDB insertion ─────────────────────────
        logger.info(f"[CHUNKING] Page/Segment {page_num}: Split into {len(chunks)} chunk(s)")

        for idx, chunk in enumerate(chunks):
            total_chunks += 1
            word_count = len(chunk.split())
            preview = chunk[:200] + "..." if len(chunk) > 200 else chunk

            logger.info("-" * 60)
            logger.info(f"  CHUNK {total_chunks} (Page {page_num}, Index {idx + 1}/{len(chunks)})")
            logger.info(f"  Words: {word_count} | Chars: {len(chunk)}")
            logger.info(f"  Preview: {preview}")

            embedding = get_embedding(chunk)
            logger.info(f"  Embedding: {'Generated (' + str(len(embedding)) + ' dims)' if embedding else 'FAILED'}")

            db_chunk = DocumentChunk(
                document_id=db_doc.id,
                file_name=file_name,
                page_number=page_num,
                content=chunk,
                content_vector=str(embedding) if embedding else None
            )
            db.add(db_chunk)

    db.commit()
    logger.info("=" * 60)
    logger.info(f"Completed! {file_name} -> {total_chunks} total chunks with vector embeddings saved to DuckDB.")
    logger.info("=" * 60)
    return db_doc
