# Database queries
from modules.pdf_chatbot.models import Documents
from sqlalchemy.ext.asyncio import AsyncSession


async def create_document(db: AsyncSession, **fields):
    document = Documents(**fields)
    db.add(document)
    await db.flush()
    return document
