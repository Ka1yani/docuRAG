from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class DocumentResponse(BaseModel):
    id: int
    file_name: str
    uploaded_at: datetime

    class Config:
        from_attributes = True

class Citation(BaseModel):
    file_name: str
    page_number: int

class ChunkResponse(BaseModel):
    content: str
    citation: Citation
    similarity_score: Optional[float] = None

class AskRequest(BaseModel):
    query: str

class AskResponse(BaseModel):
    final_answer: str
    retrieved_results: List[ChunkResponse]
    citations: List[Citation]
