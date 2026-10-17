from modules.chat.models import PromptResponse
from modules.chat.models import ChatSession
from modules.chat.schemas import AskRequest, AskResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

SUBJECT_MAX_CHARS = 80


class SessionNotFound(Exception):
    pass


class PromptResponseNotFound(Exception):
    pass


def _subject_from_prompt(prompt):
    line = " ".join(prompt.split())
    if len(line) <= SUBJECT_MAX_CHARS:
        return line
    return line[: SUBJECT_MAX_CHARS - 1].rstrip() + "…"


async def _active_session(db, user, session_id):
    session = await db.scalar(
        select(ChatSession).where(
            ChatSession.id == session_id,
            ChatSession.user == user,
            ChatSession.deleted.is_(False),
        )
    )
    if session is None:
        raise SessionNotFound(f"Session {session_id} not found")

    return session


async def ask(db: AsyncSession, user: str, data: AskRequest):
    if data.session_id is None:
        session = ChatSession(user=user, subject=_subject_from_prompt(data.prompt))
        db.add(session)
        await db.flush()
    else:
        session = await _active_session(db, user, data.session_id)
        if not session.subject:
            session.subject = _subject_from_prompt(data.prompt)
        session.updated_at = func.now()

    prompt_response = PromptResponse(
        session_id=session.id, prompt=data.prompt, role=data.role, type=data.type
    )
    db.add(prompt_response)
    await db.commit()
    await db.refresh(session)
    await db.refresh(prompt_response)
    return session, prompt_response
