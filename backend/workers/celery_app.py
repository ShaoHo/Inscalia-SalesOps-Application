from celery import Celery

from app.config import settings

celery_app = Celery(
    "salesops",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery_app.conf.update(
    task_routes={"workers.tasks.*": {"queue": "default"}},
    beat_schedule={
        "heartbeat": {
            "task": "workers.tasks.heartbeat",
            "schedule": 60.0,
        }
    },
)
