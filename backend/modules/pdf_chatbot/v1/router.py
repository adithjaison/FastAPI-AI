import asyncio
from enum import Enum

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from modules.pdf_chatbot import service as pdf_services
from modules.pdf_chatbot.schemas import DocumentResponse
from settings.dependencies import get_db, get_storage
from settings.storage import ObjectStorage
from sqlalchemy.ext.asyncio import AsyncSession

UPLOAD_SLOTS = asyncio.Semaphore(5)
router = APIRouter(prefix="/pdf_chatbot", tags=["PDF Chatbot"])


class Role(str, Enum):
    admin = "admin"
    user = "user"


@router.get("/home/{role}")
async def home(role: Role):
    return {"message": f"Hello World {role.value}"}


@router.post(
    "/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED
)
async def upload(
    file: UploadFile,
    db: AsyncSession = Depends(get_db),
    storage: ObjectStorage = Depends(get_storage),
):
    if UPLOAD_SLOTS.locked():
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "Too many uploads in progress, retry shortly",
        )
    async with UPLOAD_SLOTS:
        return await pdf_services.upload_document(db, storage, file)
