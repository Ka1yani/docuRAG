from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Sequence
from sqlalchemy.sql import func

from sqlalchemy.orm import relationship
from .db import Base

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, Sequence('document_id_seq'), primary_key=True, index=True)
    file_name = Column(String, index=True)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())

    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")

class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(Integer, Sequence('document_chunk_id_seq'), primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"))
    file_name = Column(String, index=True)
    page_number = Column(Integer, default=1)
    content = Column(Text, nullable=False)
    
    # DuckDB will cast this Text string back into an array for querying
    content_vector = Column(Text)

    document = relationship("Document", back_populates="chunks")

class SemanticCache(Base):
    __tablename__ = "semantic_cache"

    id = Column(Integer, Sequence('semantic_cache_id_seq'), primary_key=True, index=True)
    query_text = Column(Text, nullable=False)
    query_vector = Column(Text, nullable=False)
    response_text = Column(Text, nullable=False)
    retrieved_chunks_json = Column(Text, nullable=False)
    citations_json = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
