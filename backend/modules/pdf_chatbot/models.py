# SQLAlchemy models: Document, DocumentChunk, ChatSession, Message
import enum
import os

from pgvector.sqlalchemy import Vector
from settings.database import Base
from sqlalchemy import (
    BigInteger,
    Column,
    Computed,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import TSVECTOR

EMBEDDING_DIMENSIONS = int(os.environ.get("EMBEDDING_DIMENSIONS", "1024"))


class DocumentStatus(str, enum.Enum):
    UPLOADED = "UPLOADED"
    PROCESSING = "PROCESSING"
    INDEXING = "INDEXING"
    INDEXED = "INDEXED"
    FAILED = "FAILED"


class Documents(Base):
    __tablename__ = "documents"
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    object_key = Column(String, unique=True, nullable=False)
    mime_type = Column(String, nullable=False, comment="application/pdf")
    size_type = Column(BigInteger, nullable=False)
    content_hash = Column(String, nullable=False, unique=True)
    error = Column(Text)
    embedding_model = Column(Text)
    status = Column(
        Enum(DocumentStatus), nullable=False, default=DocumentStatus.UPLOADED
    )
    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class DocumentChunks(Base):
    __tablename__ = "document_chunks"
    id = Column(Integer, primary_key=True)
    document_id = Column(
        Integer,
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    chunk_index = Column(Integer, nullable=False)
    page_number = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    embedding = Column(Vector(EMBEDDING_DIMENSIONS), nullable=False)
    content_tsv = Column(
        TSVECTOR, Computed("to_tsvector('english', content)", persisted=True)
    )
    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        UniqueConstraint("document_id", "chunk_index"),
        Index(
            "ix_document_chunks_embedding_hnsw",
            "embedding",
            postgresql_using="hnsw",
            postgresql_with={"m": 16, "ef_construction": 64},
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
        Index(
            "ix_document_chunks_content_tsv", "content_tsv", postgresql_using="gin"
        ),  # NEW
    )
