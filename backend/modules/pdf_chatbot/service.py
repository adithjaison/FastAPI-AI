# Domain business logic
import hashlib
import logging
import uuid

from fastapi import HTTPException, UploadFile, status
from modules.outbox import repository as outbox
from modules.pdf_chatbot import repository
from modules.pdf_chatbot.models import Documents
from settings.storage import ObjectStorage
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

log = logging.getLogger(__name__)


async def upload_document(db: AsyncSession, storage: ObjectStorage, file: UploadFile):
    if file.content_type != "application/pdf":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Only PDF files are allowed")

    content = await file.read()
    content_hash = hashlib.sha256(content).hexdigest()
    if not content:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "File is empty")

    # Idempotency
    result = await db.execute(
        select(Documents).where(Documents.content_hash == content_hash)
    )
    existing = result.scalar_one_or_none()
    if existing:
        log.info("The file already exists: %s", f"{existing}")
        return existing

    object_key = f"{uuid.uuid4()}/{file.filename}"
    await storage.upload(object_key, content, file.content_type)
    try:
        document = await repository.create_document(
            db,
            filename=file.filename,
            object_key=object_key,
            mime_type=file.content_type,
            size_type=len(content),
            content_hash=content_hash,
        )
        outbox.add_event(
            db,
            aggregate_type="document",
            aggregate_id=document.id,
            event_type="document.uploaded",
            payload={"document_id": document.id, "object_key": object_key},
        )
        await db.commit()
    except Exception:
        await db.rollback()
        await storage.delete(object_key)
        raise
    await db.refresh(document)
    return document
