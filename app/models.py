from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.orm import relationship
from .db import Base

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    file_name = Column(String, index=True)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())

    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")

class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"))
    file_name = Column(String, index=True)
    page_number = Column(Integer, default=1)
    content = Column(Text, nullable=False)
    
    # TSVector column for full-text search
    content_vector = Column(TSVECTOR)

    document = relationship("Document", back_populates="chunks")
