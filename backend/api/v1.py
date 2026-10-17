from fastapi import APIRouter
from modules.chat.v1.router import router as chat_router
from modules.pdf_chatbot.v1.router import router as pdf_chatbot_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(pdf_chatbot_router)
api_router.include_router(chat_router)
