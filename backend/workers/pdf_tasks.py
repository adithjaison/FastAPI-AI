# Async jobs: File parsing, chunking, embedding, vector upsert
"""
process_document
  claim → download → PARSE
        → CONTENT ANALYSIS (document level)   ← new: clean, language, quality, decide branches
        → CHUNKING
        → CONTENT ANALYSIS (chunk level)      ← new: drop junk, mark graph_eligible
        → DENSE embed → SAVE (dense + sparse in the same row) → INDEXED   (searchable now)
        → write document_index_jobs rows + outbox events for the slow branches
                ├─► index_multivector task   (reads chunks from Postgres)
                └─► index_graph task         (reads graph_eligible chunks from Postgres)
"""

from datetime import timedelta

from celery.signals import worker_process_init
from celery.utils.log import get_task_logger
from modules.pdf_chatbot.embeddings import EMBEDDING_MODEL, embed_texts
from modules.pdf_chatbot.models import DocumentChunks, Documents, DocumentStatus
from modules.pdf_chatbot.parsers import PdfParseError, chunk_pages, extract_pages
from openai import APIConnectionError, InternalServerError, RateLimitError
from settings.database import SyncSessionLocal, sync_engine
from settings.storage import bucket, minio_client
from sqlalchemy import and_, delete, func, insert, or_, update
from sqlalchemy.exc import OperationalError as DatabaseUnavailable
from urllib3.exceptions import HTTPError as StorageUnavailable
from workers.celery_app import app as celery_app

log = get_task_logger(__name__)
TRANSIENT_ERRORS = (
    StorageUnavailable,
    DatabaseUnavailable,
    APIConnectionError,
    RateLimitError,
    InternalServerError,
)

STALE_CLAIM_AFTER = timedelta(minutes=15)
IN_PROGRESS = (DocumentStatus.PROCESSING, DocumentStatus.INDEXING)


@worker_process_init.connect
def _reset_db_pool(**_):
    sync_engine.dispose(close=False)


def download(object_key):
    response = minio_client.get_object(bucket_name=bucket, object_name=object_key)
    try:
        return response.read()
    finally:
        response.close()
        response.release_conn()


def save_chunks(document_id, chunks, vectors):
    rows = [
        {"document_id": document_id, **chunk, "embedding": vector}
        for chunk, vector in zip(chunks, vectors, strict=True)
    ]
    with SyncSessionLocal.begin() as db:
        db.execute(
            delete(DocumentChunks).where(DocumentChunks.document_id == document_id)
        )
        db.execute(insert(DocumentChunks), rows)
        db.execute(
            update(Documents)
            .where(Documents.id == document_id)
            .values(
                status=DocumentStatus.INDEXED,
                embedding_model=EMBEDDING_MODEL,
                error=None,
            )
        )


def set_status(document_id, status: DocumentStatus, error: str | None = None):
    with SyncSessionLocal.begin() as db:
        db.execute(
            update(Documents)
            .where(Documents.id == document_id)
            .values(status=status, error=error)
        )


def claim(document_id):
    stmt = (
        update(Documents)
        .where(
            Documents.id == document_id,
            or_(
                Documents.status == DocumentStatus.UPLOADED,
                and_(
                    # recover documents left behind by a crashed worker
                    Documents.status.in_(IN_PROGRESS),
                    Documents.updated_at < func.now() - STALE_CLAIM_AFTER,
                ),
            ),
        )
        .values(status=DocumentStatus.PROCESSING, error=None)
        .returning(Documents.id)
    )
    with SyncSessionLocal.begin() as db:
        return db.execute(stmt).scalar_one_or_none() is not None


@celery_app.task(bind=True, name="pdf_chatbot.process_document", max_retries=5)
def process_document(self, document_id, object_key):
    if not claim(document_id):
        log.info("Document %s already claimed or processed; skipping", document_id)
        return {"document_id": document_id, "skipped": True}

    try:
        data = download(object_key)
        chunks = chunk_pages(extract_pages(data))
        if not chunks:
            raise PdfParseError("No extractable text (scanned/image-only PDF?")

        set_status(document_id, DocumentStatus.INDEXING)
        vectors = embed_texts([c["content"] for c in chunks])
        save_chunks(document_id, chunks, vectors)
        log.info("Document %s indexed: %s chunks", document_id, len(chunks))

        return {"document_id": document_id, "chunks": len(chunks)}
    except TRANSIENT_ERRORS as exc:
        if self.request.retries >= self.max_retries:
            set_status(
                document_id, DocumentStatus.FAILED, f"Gve up after retires: {exc}"
            )
            raise
        set_status(document_id, DocumentStatus.UPLOADED)
        raise self.retry(exc=exc, countdown=5 * 2**self.request.retries)
    except Exception as exc:
        set_status(document_id, DocumentStatus.FAILED, str(exc))
        raise
