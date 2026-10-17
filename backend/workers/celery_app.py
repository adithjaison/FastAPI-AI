# Worker instance configuration & broker bindings
import os

from celery import Celery

app = Celery(
    "backend",
    broker=os.environ["CELERY_BROKER_URL"],
    backend=os.environ["CELERY_RESULT_BACKEND"],
    include=["workers.pdf_tasks"],
)


app.conf.update(
    result_expires=3600,
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,
    broker_connection_retry_on_startup=True,
    task_soft_time_limit=600,
    task_time_limit=660,
)

if __name__ == "__main__":
    app.start()
