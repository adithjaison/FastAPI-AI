from datetime import datetime
from typing import Any

from modules.chat.models import MessageRole
from pydantic import BaseModel, ConfigDict, Field


class SessionCreate(BaseModel):
    subject: str | None = Field(default=None, max_length=200)


class SessionUpdate(BaseModel):
    subject: str | None = Field(min_length=1, max_length=200)


class SessionResponse(BaseModel):
    id: int
    user: str
    subject: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AskRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=10_000)
    session_id: int | None = None
    role: MessageRole = MessageRole.USER
    type: str = Field(default="text", min_length=1, max_length=20)


class PromptResponseOut(BaseModel):
    id: int

    session_id: int
    prompt: str
    response: str | None
    role: MessageRole
    type: str
    functions_called: list[Any] | dict[str, Any] | None
    created_at: datetime
    updated_at: datetime


class AskResponse(BaseModel):
    session: SessionResponse
    prompt_response: PromptResponseOut


class PromptResponseCreate(BaseModel):
    prompt: str
