# Global FastAPI dependencies (get_db, get_redis, get_llm_client)
import os

from settings.database import AsyncSessionLocal
from settings.storage import ObjectStorage, storage

DEFAULT_USER = os.environ.get("DEFAULT_USER", "admin")


async def get_db():
    async with AsyncSessionLocal() as db_session:
        yield db_session


def get_storage() -> ObjectStorage:
    return storage


def get_current_user():
    return DEFAULT_USER


"""
from settings.database import SessionLocal


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
"""
