import os
import shutil
from fastapi import FastAPI, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.db import get_db, init_db
from app.models import Document
from app.schemas import AskRequest, AskResponse, DocumentResponse, Citation
from app.services.document_processor import process_and_store_document
from app.services.retrieval import retrieve_context
from app.services.llm_service import generate_answer

app = FastAPI(title="docuRAG", version="1.0.0")

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.on_event("startup")
def startup_event():
    # Initialize the database and ensure pg_trgm extension is active
    init_db()

@app.post("/upload", status_code=201)
def upload_document(file: UploadFile = File(...), db: Session = Depends(get_db)):
    valid_extensions = [".pdf", ".doc", ".docx", ".txt"]
    _, ext = os.path.splitext(file.filename.lower())
    if ext not in valid_extensions:
        raise HTTPException(status_code=400, detail=f"Unsupported file type. Valid types are: {', '.join(valid_extensions)}")
    
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    
    # Save file to disk
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    try:
        # Process and save to PostgreSQL
        doc = process_and_store_document(file_path, file.filename, db)
        return {"message": "File processed successfully", "document_id": doc.id, "file_name": doc.file_name}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ask", response_model=AskResponse)
def ask_question(request: AskRequest, db: Session = Depends(get_db)):
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
        
    # 1. Retrieve Context using FTS and Trigrams
    chunks = retrieve_context(request.query, db, top_k=5)
    
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
    answer = generate_answer(request.query, chunks)
    
    # Fallback to empty citations if the Local LLM says answer isn't found
    if "Answer not found in provided documents." in answer:
        citations = []
        
    return AskResponse(
        final_answer=answer,
        retrieved_results=chunks,
        citations=citations
    )

@app.get("/documents", response_model=List[DocumentResponse])
def get_documents(db: Session = Depends(get_db)):
    docs = db.query(Document).order_by(Document.uploaded_at.desc()).all()
    return docs
