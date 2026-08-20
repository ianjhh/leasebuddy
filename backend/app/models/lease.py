import uuid
from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import Column, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.config import settings
from app.models.base import Base


class LeaseDocument(Base):
    """
    Represents an uploaded lease PDF in our database.
    """
    __tablename__ = "lease_documents" # The actual name of the table in Postgres

    # We use UUIDs instead of standard 1,2,3 IDs for better security
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    filename = Column(String, nullable=False)
    s3_url = Column(String, nullable=True) # Where the physical file is stored in AWS
    status = Column(String, default="processing") # "processing", "completed", "failed"
    
    # Store extra flexible data (like page count, file size) in a JSON column
    metadata_ = Column("metadata", JSONB, default={}) 
    
    created_at = Column(DateTime, default=datetime.utcnow)

    # Establish a relationship with the chunks (One Lease has Many Chunks)
    chunks = relationship("LeaseChunk", back_populates="document", cascade="all, delete-orphan")


class LeaseChunk(Base):
    """
    When we process a 50-page lease, we break it into small "chunks" (e.g. 500 words each).
    We turn each chunk into a Vector Embedding.
    """
    __tablename__ = "lease_chunks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Link back to the parent LeaseDocument
    document_id = Column(UUID(as_uuid=True), ForeignKey("lease_documents.id"), nullable=False)
    
    # The actual text of this paragraph/chunk
    text_content = Column(String, nullable=False)
    
    # THE MAGIC HAPPENS HERE: This column stores our 768-dimension vector embedding!
    embedding = Column(Vector(settings.VECTOR_DIMENSION), nullable=False)
    
    # Extra data like {"page_number": 4, "section_title": "Pets"}
    chunk_metadata = Column(JSONB, default={})

    # Link back to the parent Document
    document = relationship("LeaseDocument", back_populates="chunks")