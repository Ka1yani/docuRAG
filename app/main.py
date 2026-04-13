import os
import shutil
from fastapi import FastAPI, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from typing import List
import time
import string
import random
from fastapi import Request
from app.logger import logger

from app.db import get_db, init_db
from app.models import Document, DocumentChunk
from app.schemas import AskRequest, AskResponse, DocumentResponse, Citation
from app.services.document_processor import process_and_store_document
from app.services.retrieval import retrieve_context
from app.services.llm_service import generate_answer
from app.services.cache_service import check_semantic_cache, store_semantic_cache
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="docuRAG", version="1.0.0")

# Allow the Next.js frontend to communicate with this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

def make_progress_bar(percent: float, length: int = 20) -> str:
    filled = int(length * percent / 100)
    bar = '█' * filled + '-' * (length - filled)
    return f"[{bar}] {percent:5.1f}%"

@app.middleware("http")
async def log_requests(request: Request, call_next):
    idem = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    logger.info(f"Req [{idem}] {request.method} {request.url.path}")
    start_time = time.time()
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    logger.info(f"Req [{idem}] Completed in {process_time:.2f}s (Status: {response.status_code})")
    
    response.headers["X-Request-ID"] = idem
    return response

@app.on_event("startup")
def startup_event():
    # Initialize the database
    init_db()

@app.post("/upload", status_code=201)
def upload_document(file: UploadFile = File(...), db: Session = Depends(get_db)):
    valid_extensions = [".pdf", ".doc", ".docx", ".txt", ".mp3", ".wav", ".m4a", ".png", ".jpg", ".jpeg", ".webp"]
    _, ext = os.path.splitext(file.filename.lower())
    if ext not in valid_extensions:
        raise HTTPException(status_code=400, detail=f"Unsupported file type. Valid types are: {', '.join(valid_extensions)}")
    
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    
    # Save file to disk
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    try:
        # Process and save to DuckDB
        logger.info(f"Starting processing for file: {file.filename}")
        doc = process_and_store_document(file_path, file.filename, db)
        logger.info(f"Successfully processed and stored {doc.file_name}")
        return {"message": "File processed successfully", "document_id": doc.id, "file_name": doc.file_name}
    except Exception as e:
        logger.error(f"Failed to process {file.filename}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ask", response_model=AskResponse)
def ask_question(request: AskRequest, db: Session = Depends(get_db)):
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
        
    # 0. Check Enterprise Semantic Cache
    t_cache = time.time()
    cached_data, embedded_query = check_semantic_cache(request.query, db)
    if cached_data[0]:
        cache_time = time.time() - t_cache
        logger.info(f"=== Enterprise Cache Execution ===")
        logger.info(f"  Bypassed DuckDB & Ollama in {cache_time:.2f}s!")
        return AskResponse(
            final_answer=cached_data[0],
            retrieved_results=cached_data[1],
            citations=cached_data[2]
        )
        
    # 1. Retrieve Context using FTS and Trigrams
    t0 = time.time()
    chunks = retrieve_context(request.query, db, top_k=3, embedded_query=embedded_query)
    duckdb_time = time.time() - t0
    
    # 2. Extract Citations
    citations = []
    seen = set()
    for chunk in chunks:
        cit_key = (chunk.citation.file_name, chunk.citation.page_number)
        if cit_key not in seen:
            seen.add(cit_key)
            citations.append(Citation(file_name=cit_key[0], page_number=cit_key[1]))
            
    # 3. Handle Hailucination Prevention logic
    if not chunks:
        return AskResponse(
            final_answer="Answer not found in provided documents.",
            retrieved_results=[],
            citations=[]
        )
        
    # 4. Generate Answer via Ollama
    t1 = time.time()
    answer = generate_answer(request.query, chunks)
    llm_time = time.time() - t1
    
    # Profiling Logs
    total_measured = duckdb_time + llm_time
    if total_measured > 0:
        duck_pct = (duckdb_time / total_measured) * 100
        llm_pct = (llm_time / total_measured) * 100
        logger.info("=== Execution Breakdown ===")
        logger.info(f"  DuckDB : {make_progress_bar(duck_pct)} ({duckdb_time:.2f}s)")
        logger.info(f"  Ollama : {make_progress_bar(llm_pct)} ({llm_time:.2f}s)")
        logger.info("============================")
    
    # Fallback to empty citations if the Local LLM says answer isn't found
    if "Answer not found in provided documents." in answer:
        citations = []
    else:
        # Cache successful semantic generation
        if embedded_query:
            store_semantic_cache(request.query, embedded_query, answer, chunks, citations, db)
        
    return AskResponse(
        final_answer=answer,
        retrieved_results=chunks,
        citations=citations
    )

@app.get("/documents", response_model=List[DocumentResponse])
def get_documents(db: Session = Depends(get_db)):
    docs = db.query(Document).order_by(Document.uploaded_at.desc()).all()
    return docs

@app.delete("/documents/{document_id}")
def delete_document(document_id: int, db: Session = Depends(get_db)):
    # 1. Fetch document metadata
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    file_name = doc.file_name
    file_path = os.path.join(UPLOAD_DIR, file_name)

    try:
        # 2. Complete DuckDB Cascade Wipe 
        # Delete child chunks mathematically bounding the vector RAG arrays first
        db.query(DocumentChunk).filter(DocumentChunk.document_id == document_id).delete(synchronize_session=False)
        db.commit() # Explicitly commit here to release the foreign key constraint in DuckDB
        
        # 3. Drop primary meta-record
        db.delete(doc)
        db.commit()

        # 4. Physically remove the file to prevent server rotting
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"Physically deleted {file_name} from disk.")
            
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to cascade delete {file_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Database cascade deletion failed: {str(e)}")

    return {"message": "Document and all associated chunks permanently deleted."}
