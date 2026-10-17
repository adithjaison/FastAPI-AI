import enum

from settings.database import Base
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB

DEFAULT_USER = "admin"


class MessageRole(str, enum.Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ChatSession(Base):
    __tablename__ = "chat_sessions"
    id = Column(Integer, primary_key=True)
    user = Column(
        String(150), nullable=False, default=DEFAULT_USER, server_default=DEFAULT_USER
    )
    subject = Column(String(200))
    deleted = Column(
        Boolean, nullable=False, default=False, server_default=text("false")
    )
    deleted_at = Column(DateTime(timezone=True))
    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
    __table_args__ = (
        Index(
            "ix_chat_sessions_user_updated_active",
            "user",
            "updated_at",
            postgresql_where=text("NOT deleted"),
        ),
    )


class PromptResponse(Base):
    __tablename__ = "prompt_responses"
    id = Column(Integer, primary_key=True)
    session_id = Column(
        Integer,
        ForeignKey("chat_sessions.id", ondelete="CASCADE"),
        nullable=False,
    )
    prompt = Column(Text, nullable=False)
    response = Column(Text)
    role = Column(
        Enum(
            MessageRole,
            name="message_role",
            values_callable=lambda e: [m.value for m in e],
        ),
        nullable=False,
        default=MessageRole.USER,
        server_default=MessageRole.USER.value,
    )
    type = Column(String(20), nullable=False, default="text", server_default="text")
    functions_called = Column(JSONB)
    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    __table_args__ = (
        Index("ix_prompt_responses_session_created", "session_id", "created_at"),
    )
