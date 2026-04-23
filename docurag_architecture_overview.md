# DocuRAG Architecture Overview

The following document represents the finalized technical snapshot of the **DocuRAG** codebase. This functions as a "cheat sheet" for spinning up new AI or human developers into the existing system state.

## 1. High-Level Stack
*   **Backend:** FastAPI (Python 3.14 compatible, Windows-Native).
*   **Frontend:** Next.js (React), styled natively without Tailwind relying on raw CSS glassmorphic aesthetic pipelines.
*   **Vector Datastore:** DuckDB embedded via `duckdb-engine` attached to SQLAlchemy.
*   **AI Runner:** `Ollama` running as a localized service providing both Semantic Vector Embeddings (`nomic-embed-text`) and Language Generation.

## 2. The Ingestion Engine (`app/services/document_processor.py`)
DocuRAG natively parses an incredibly wide array of omni-modal formats, executing varying processor pipelines. All chunks are immediately vectored by `nomic-embed-text` and inserted sequentially into DuckDB.
*   **PDFs/Word (`.pdf`, `.doc`, `.docx`):** Extracted via generic recursive Python parsers (`pypdf`, `python-docx`).
*   **Audio (`.mp3`, `.wav`, `.m4a`):** Processed dynamically through `faster-whisper` locked to `int8` CPU precision, with native speech timestamps injected explicitly into the parsed document string chunks.
*   **Images (`.png`, `.jpg`):** Handled by a state-of-the-art HuggingFace Vision Language Model pipeline (`deepseek-ai/DeepSeek-OCR-2`).
    *   **Crucial State Pattern:** The VLM model sits behind a **Lazy Singleton** (`_load_deepseek_model`). It will strictly *not* boot into CPU memory until an image is actually ingested. 
    *   **Windows Architecture Hack:** Because Python 3.14 cannot natively compile complex Hugging Face Rust architectures (`tokenizers<0.21`, `flash-attn`), the codebase enforces `transformers<5` and specifically applies a **Monkey Patch** `MockAttention` class directly over `LlamaFlashAttention2`. This bypasses compiler errors seamlessly and forces the Heavy weights smoothly onto Windows CPU limits (`device_map="cpu"`, `torch.float32`).

## 3. The Retrieval Engine (`app/services/retrieval.py`)
The system strictly enforces ChatGPT-like contextual isolation.
*   **Document-Tethering:** The `/ask` endpoint requires a `document_id`. The DuckDB SQL restricts generic semantic search `array_cosine_similarity(content_vector, embed) > 0.65` heavily alongside `AND document_id = :doc_id`. This creates a solid sandbox preventing data-bleed from other documents mathematically.
*   **Anti-Hallucination:** DuckDB has been configured with an elevated mathematical relevance threshold (`0.65`). If context vectors fall below this probability, DuckDB forces an empty list `[]` to the LLM, which triggers the backend rule instructing the model to spit out explicitly: `"Answer not found in provided documents."`

## 4. Enterprise Semantic Caching (`app/services/cache_service.py`)
To limit token destruction and Local VRAM spiking, DocuRAG deploys strict semantic caching locally alongside standard DuckDB operations.
*   **Isolated Namespaces:** Each semantic vector stored dynamically prefixes its key with the exact Context `DOC_ID:[int]`. If two drastically different chat threads ask identical queries across different document vectors, they will *not* pull from the generic cache, preventing cross-contamination.

## 5. The Database Schema (`app/models.py` & `app/main.py`)
*   **Tables:** `documents`, `document_chunks` (containing generic Text payload strings for DuckDB Arrays), and `semantic_cache`.
*   **IMPORTANT ARCHITECTURE QUIRK:** You must never apply generic SQLAlchemy Cascade indexing (`index=True`) on primary relationships. DuckDB `duckdb_engine` suffers from massive internal OLAP fatal `Index Deletion` exceptions when trying to aggressively delete object models.
*   **Database Management:** For dynamic cleanup via the backend API endpoints (`DELETE /documents/{id}`), DocuRAG relies purely on `text()` RAW SQL cascading. Do not attempt `db.delete(doc)`. Additionally, the Uvicorn `startup_event` actively scans DuckDB to verify `ix_` indexes aren't secretly corrupting the file, healing them actively silently if they are.

## 6. Frontend Execution Context
The Next.js Application manages conversational persistence entirely off generic `localStorage` caching logic. When a user queries from the active context menu, the Frontend passes the URL Context binding and handles raw array mapping for Citations dynamically.

___

## 1. 2-Minute Project Explanation 
**DocuRAG** is a fully localized, privacy-first "Chat with your Documents" application. Think of it like a personalized, private ChatGPT that can specifically read your files and answer questions about them without sending your data to the cloud.

*   **Non-Technical Execution:** A user opens the beautiful, glassmorphic Next.js web application and uploads a file. The application accepts almost anything—Text documents (PDFs, Word files), Audio (MP3s), and even complex Images (Handwritten notes or Graphs). Behind the scenes, the system reads the files, breaks them down into tiny context blocks, and locks them inside a local database. When the user asks a question, the application mathematically searches for the most relevant blocks of information, feeds them to a Local AI, and replies with a highly accurate answer while actively citing the exact paragraph or timestamp it found the information in.
*   **Technical Edge:** It deploys an advanced Retrieval-Augmented Generation (RAG) pipeline utilizing DuckDB for rapid, embedded SQL vector-searches. It operates entirely on-premise using Ollama (Llama/Mistral) for LLM reasoning and Nomic for embeddings. Furthermore, it explicitly handles strict anti-hallucination sandboxing—if the database math doesn't strongly overlap with the user's question, it explicitly forces the LLM to admit it doesn't know the answer, guaranteeing zero fake information.

___

## 2. Deep Technical Overview

### The Tech Stack
*   **Backend:** FastAPI (Python 3.14 compatible, Windows-Native).
*   **Frontend:** Next.js (React), styled natively relying on raw CSS glassmorphic aesthetic pipelines.
*   **Vector Datastore:** DuckDB embedded via `duckdb-engine` attached to SQLAlchemy.
*   **AI Runner:** `Ollama` running as a localized service providing both Semantic Vector Embeddings (`nomic-embed-text`) and Language Generation.

### Advanced Architectural Details
*   **Enterprise Semantic Caching:** To limit token destruction and Local VRAM spiking, DocuRAG deploys strict semantic caching locally alongside standard DuckDB operations. Each semantic vector stored dynamically prefixes its key with the exact Context `DOC_ID:[int]`. If two drastically different chat threads ask identical queries, they will *not* pull from the generic cache, preventing cross-contamination.
*   **Tethering Sandbox:** The `/ask` endpoint strictly enforces `document_id` binding. The DuckDB SQL restricts generic semantic search `array_cosine_similarity(content_vector, embed) > 0.65` alongside `AND document_id = :doc_id`. This creates a mathematically solid sandbox preventing data-bleed from other uploaded documents.
*   **Hardware Fallback Patching:** Because native Windows Python cannot compile Hugging Face Rust architectures (`tokenizers<0.21`, `flash-attn`), the codebase enforces `transformers<5` and specifically applies a **Monkey Patch** `MockAttention` class directly over `LlamaFlashAttention2`. This bypasses compiler errors seamlessly and forces the Heavy weights smoothly onto Windows CPU limits (`device_map="cpu"`, `torch.float32`).
*   **Database Anomaly Healing:** DuckDB `duckdb_engine` suffers from massive internal OLAP fatal `Index Deletion` exceptions when trying to aggressively delete object sequence models. DocuRAG relies purely on `text()` RAW SQL cascading for deletions. Additionally, the Uvicorn `startup_event` actively scans DuckDB to explicitly execute `DROP INDEX` against corrupt tables upon server reloads.

___

## 3. Step-by-Step Architecture Flow

### Phase 1: Upload & Processing
1.  **Ingestion:** The user uploads a file through the React UI. FastAPI accepts the `UploadFile` and writes it to the local `/uploads` directory.
2.  **Format Routing (`app/services/document_processor.py`):**
    *   *Text (`.pdf`, `.docx`):* Parsed generic strings.
    *   *Audio (`.mp3`):* Handed to `faster-whisper`. Audio is transcribed natively on CPU to `int8` precision, injecting exact timestamps (e.g., `[Audio Segment 01:23 - 01:45]: hello`) back into the string payload.
    *   *Images (`.png`, `.jpg`):* Handed to a **Lazy-Loaded** `DeepSeek-OCR-2` Vision Language Model. The model boots silently, extracts complex formatting (Full markdown layouts/tables), and returns structural string payloads.
3.  **Chunking:** The extracted strings are token-sliced via `chunk_text(word_chunk_size=400)`.
4.  **Embedding:** Every individual chunk is pushed to `Ollama` (`nomic-embed-text`) to generate a highly granular numeric Floating-Point Vector.

### Phase 2: Storage
1.  **DuckDB Insertion:** The vectors and their raw string payload (plus metadata like `page_number` or `document_id`) are ingested into DuckDB via SQLAlchemy.
2.  **Array Commitment:** DuckDB natively maps the long generic string vector lists into mathematically searchable multidimensional arrays.

### Phase 3: Retrieval
1.  **Query Trigger:** The user asks a question in the UI (bound to a specific Document).
2.  **Cache Verification:** The backend instantly checks if that *literal mathematical embedding vector* exists inside the `SemanticCache` table for that specific document. If yes, it completely bypasses the LLM and answers immediately!
3.  **Vector Search:** If no cache exists, the query itself is vectorized. DuckDB executes a strict `array_cosine_similarity` check against the table arrays.
4.  **Anti-Hallucination Gate:** Any matching chunk that falls underneath the `0.65` Cosine Similarity threshold is automatically stripped out. If all chunks fail the check, the query chain instantly aborts.

### Phase 4: Generation & Response
1.  **LLM Synthesizing:** Only the high-fidelity matching chunks are aggregated into a single formatted string context. This context is shoved alongside the user's question into Ollama's local LLM generator via a highly-strict, hallucination-resistant System Prompt.
2.  **Citation Mapping:** The backend aggregates exactly which pages/timestamps the chunks belong to (`chunk.citation.page_number`), generating explicit reference links.
3.  **Delivery:** The generated output is saved back into the exact Semantic Cache and explicitly streamed back to the Next.js UI using structured JSON.
