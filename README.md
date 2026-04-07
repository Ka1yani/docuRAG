# docuRAG

docuRAG is a local, end-to-end Retrieval-Augmented Generation (RAG) system built with FastAPI, **DuckDB**, and Mistral (via Ollama).
It relies on **Semantic Vector Embeddings** using `nomic-embed-text` and DuckDB's native high-performance array similarities to retrieve conceptually relevant context.

## Prerequisites

1. **Python 3.10+** (Recommended)
2. **Ollama** running locally on port 11434.
*(No Docker required! The database is completely embedded inside Python).*

## Setup Instructions

### 1. Database Configuration (100% Embedded)
DuckDB runs seamlessly without servers or Docker. Ensure your `.env` is configured to create a local `.duckdb` file:
```env
DATABASE_URL=duckdb:///docurag_data.duckdb
OLLAMA_URL=http://localhost:11434/api/generate
OLLAMA_EMBED_URL=http://localhost:11434/api/embeddings
MODEL_NAME=mistral:7b
```

### 2. Install Dependencies
Create a virtual environment and install the required packages:
```bash
python -m venv .venv
# Activate environment (Windows)
.venv\Scripts\activate
# Activate environment (Mac/Linux)
source .venv/bin/activate

pip install -r requirements.txt
```

### 3. Setup Ollama Models
Make sure Ollama is installed from [ollama.com](https://ollama.com).
Pull the necessary models before running the application:
```bash
ollama pull mistral:7b
ollama pull nomic-embed-text
```

### 4. Running the Application
The backend FastAPI server handles database initialization automatically on startup.

**Start the Backend (FastAPI):**
```bash
uvicorn app.main:app --reload --port 8000
```
Swagger UI will be available at: http://localhost:8000/docs

**Start the Frontend (Streamlit) in another terminal:**
```bash
streamlit run streamlit_app.py
```

### 5. API Endpoints

* `POST /upload` - Upload PDF, DOC, DOCX, or TXT. Parses text, creates semantic embeddings via `nomic-embed-text`, and stores them natively in DuckDB.
* `POST /ask` - Pass `{"query": "your question"}`. Embeds your question, calculates pure Cosine Similarity (`array_cosine_similarity()`) in analytical SQL to fetch chunks, and prompts Mistral for generated answers citing its sources.
* `GET /documents` - Lists all processed files.

### 6. Testing Script
Run the automated testing queries to query 20 different concepts once some documents are uploaded:
```bash
python test_questions.py
```
