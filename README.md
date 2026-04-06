# docuRAG

docuRAG is a local, end-to-end Retrieval-Augmented Generation (RAG) system built with FastAPI, PostgreSQL (`pgvector`), and Mistral (via Ollama).
It relies on **Semantic Vector Embeddings** using `nomic-embed-text` and Postgres's `pgvector` extension to retrieve conceptually relevant context.

## Prerequisites

1. **Python 3.10+** (Recommended)
2. **Docker Desktop** (To easily run the PostgreSQL vector database)
3. **Ollama** running locally on port 11434.

## Setup Instructions

### 1. Database Configuration (Docker)
Start a PostgreSQL container pre-configured with the `pgvector` extension by running the following command:
```bash
docker run -d --name postgres-vector -e POSTGRES_PASSWORD=mysecretpassword -p 5450:5432 pgvector/pgvector:pg16
```

Then, update your `.env` file to point to the new container on port `5450` (It connects to the default `postgres` database inside the container):
```env
DATABASE_URL=postgresql://postgres:mysecretpassword@localhost:5450/postgres
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

* `POST /upload` - Upload PDF, DOC, DOCX, or TXT. Parses text, creates semantic embeddings via `nomic-embed-text`, and stores them in PostgreSQL `pgvector` columns.
* `POST /ask` - Pass `{"query": "your question"}`. Embeds your question, calculates pure Cosine Distance (`<=>`) in SQL to fetch chunks, and prompts Mistral for generated answers citing its sources.
* `GET /documents` - Lists all processed files.

### 6. Testing Script
Run the automated testing queries to query 20 different concepts once some documents are uploaded:
```bash
python test_questions.py
```
