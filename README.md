# docuRAG

docuRAG is a local, end-to-end Retrieval-Augmented Generation (RAG) system built with FastAPI, PostgreSQL, and Mistral (via Ollama).
It relies **exclusively** on PostgreSQL's Full-Text Search (`tsvector`) and Trigram matching (`pg_trgm`) to retrieve relevant context.

## Prerequisites

1. **Python 3.10+** (Recommended)
2. **PostgreSQL** with `pg_trgm` extension capability.
3. **Ollama** running locally on port 11434.

## Setup Instructions

### 1. Database Configuration
Ensure PostgreSQL is running. 
A `.env` file is included in this directory. By default it expects:
```env
DATABASE_URL=postgresql://postgres:Kalyani_1998@localhost:5432/rag_db
OLLAMA_URL=http://localhost:11434/api/generate
MODEL_NAME=mistral:7b
```
*Note: Make sure the `rag_db` database actually exists before running the app. You can create it via pgAdmin or `createdb rag_db`.*

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

### 3. Setup Ollama
Make sure Ollama is installed from [ollama.com](https://ollama.com).
Pull the `mistral` model before running the application:
```bash
ollama pull mistral
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

* `POST /upload` - Upload PDF, DOC, DOCX, or TXT. Parses and chunks content into PostgreSQL `tsvector` columns.
* `POST /ask` - Pass `{"query": "your question"}`. Uses FTS and pg_trgm for context retrieval, prompting Mistral to answer only based on the retrieved context with Hallucination limits.
* `GET /documents` - Lists all processed files.

### 6. Testing Script
Run the automated testing queries to query 20 different concepts once some documents are uploaded:
```bash
python test_questions.py
```
