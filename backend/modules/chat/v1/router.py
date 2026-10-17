from http.client import HTTPException

from modules.chat.schemas import PromptResponseOut, SessionResponse
from fastapi import APIRouter, Depends, status
from modules.chat import services as chat_services
from modules.chat.schemas import AskRequest, AskResponse
from settings.dependencies import get_current_user, get_db
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/prompts", tags=["Chats"])
NOT_FOUND = (chat_services.SessionNotFound, chat_services.PromptResponseNotFound)


def _not_found(exc: Exception):
    return HTTPException(status.HTTP_404_NOT_FOUND, str(exc))


@router.post("/ask", response_model=AskResponse, status_code=status.HTTP_201_CREATED)
async def ask(
    body: AskRequest,
    db: AsyncSession = Depends(get_db),
    user: str = Depends(get_current_user),
):
    try:
        session, prompt_response = await chat_services.ask(db, user, body)
    except NOT_FOUND as exc:
        raise _not_found(exc) from exc
    return AskResponse(
        session=SessionResponse.model_validate(session),
        prompt_response=PromptResponseOut.model_validate(prompt_response),
    )
