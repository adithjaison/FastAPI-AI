from modules.outbox.models import OutboxEvent
from sqlalchemy.ext.asyncio import AsyncSession


def add_event(
    db: AsyncSession,
    *,
    aggregate_type: str,
    aggregate_id: int,
    event_type: str,
    payload: dict
):
    event = OutboxEvent(
        aggregate_type=aggregate_type,
        aggregate_id=aggregate_id,
        event_type=event_type,
        payload=payload,
    )
    db.add(event)
    return event
