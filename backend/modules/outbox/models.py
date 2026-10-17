import enum

from settings.database import Base
from sqlalchemy import Column, DateTime, Enum, Index, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB


class OutboxStatus(str, enum.Enum):
    PENDING = "PENDING"
    PUBLISHED = "PUBLISHED"
    FAILED = "FAILED"


class OutboxEvent(Base):
    __tablename__ = "outbox_events"
    id = Column(Integer, primary_key=True)
    aggregate_type = Column(String, nullable=False)
    aggregate_id = Column(Integer, nullable=False)
    event_type = Column(String, nullable=False)
    payload = Column(JSONB, nullable=False)
    status = Column(
        Enum(OutboxStatus, name="outbox_status"),
        nullable=False,
        default=OutboxStatus.PENDING,
        server_default=OutboxStatus.PENDING.value,
    )
    attempts = Column(Integer, nullable=False, default=0, server_default="0")
    last_error = Column(Text)
    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    published_at = Column(DateTime(timezone=True))

    __table_args__ = (
        Index(
            "ix_outbox_events_pending",
            "created_at",
            postgresql_where=(status == OutboxStatus.PENDING),
        ),
    )
