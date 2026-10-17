import asyncio
import logging

from modules.outbox.models import OutboxEvent, OutboxStatus
from settings.database import AsyncSessionLocal
from sqlalchemy import func, select
from sqlalchemy.orm.util import eval_name_only
from workers.celery_app import app as celery_app

SEND_CONCURRENCY = 10
MAX_BACKOFF_SECONDS = 60
MAX_ATTEMPTS = 5
POLL_SECONDS = 2
BATCH_SIZE = 50
ROUTES = {"document.uploaded": "pdf_chatbot.process_document"}
log = logging.getLogger("outbox.relay")

from kombu.exceptions import OperationalError as BrokerUnavailable


async def fetch_pending(db):
    result = await db.scalars(
        select(OutboxEvent)
        .where(OutboxEvent.status == OutboxStatus.PENDING)
        .order_by(OutboxEvent.created_at)
        .limit(BATCH_SIZE)
        .with_for_update(skip_locked=True)
    )
    return list(result.all())


async def send_all(jobs):
    """
    Send every (event, task_name) to RabbitMQ, at most SEND_CONCURRENCY at a time.

    Returns one result per job, in the same order:
      None      → sent successfully
      Exception → that send failed (gather collects it instead of stopping the others)
    """
    semaphore = asyncio.Semaphore(SEND_CONCURRENCY)

    async def send(event, task_name):
        async with semaphore:
            await asyncio.to_thread(
                celery_app.send_task,
                task_name,
                kwargs=event.payload,
                task_id=f"outbox-{event.id}",
            )

    return await asyncio.gather(
        *(send(event, task_name) for event, task_name in jobs), return_exceptions=True
    )


def mark_published(event):
    event.status = OutboxStatus.PUBLISHED
    event.published_at = func.now()


def mark_failed_attempt(event, error):
    event.attempts += 1
    event.last_error = str(error)
    if event.attempts >= MAX_ATTEMPTS:
        event.status = OutboxStatus.FAILED
    log.error(
        "Failed to publish outbox event %s (attempt %s): %s",
        event.id,
        event.attempts,
        error,
    )


def mark_unroutable(event: OutboxEvent):
    event.status = OutboxStatus.FAILED
    event.last_error = f"No route for event type {event.event_type!r}"
    log.error("Outbox event %s has no route: %s", event.id, event.event_type)


async def publish_batch():
    async with AsyncSessionLocal() as db, db.begin():
        events = await fetch_pending(db)

        jobs = []
        for event in events:
            task_name = ROUTES.get(event.event_type)
            if task_name is None:
                mark_unroutable(event)
            else:
                jobs.append((event, task_name))
        if not jobs:
            return 0
        results = await send_all(jobs)

        published = 0
        broker_down = False
        for (event, _), result in zip(jobs, results):
            if result is None:
                mark_published(event)
                published += 1
            elif isinstance(result, BrokerUnavailable):
                broker_down = True
            else:
                mark_failed_attempt(event, result)
        if broker_down:
            log.warning(
                "Broker unavailable; %s event(s) left PENDING for the next loop",
                sum(isinstance(r, BrokerUnavailable) for r in results),
            )
        return published


async def main():
    logging.basicConfig(level=logging.INFO)
    log.info(
        "Outbox relay started (batch=%s, concurrency=%s", BATCH_SIZE, SEND_CONCURRENCY
    )

    backoff = 1
    while True:
        try:
            published = await publish_batch()
            backoff = 1
        except Exception:
            log.exception("Outbox batch filed; retrying in %ss", backoff)
            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, MAX_BACKOFF_SECONDS)
            continue

        if published:
            log.info("Published %s event(s)", published)
        else:
            await asyncio.sleep(POLL_SECONDS)


if __name__ == "__main__":
    asyncio.run(main())
