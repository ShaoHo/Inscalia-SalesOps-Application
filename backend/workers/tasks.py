from datetime import datetime

from workers.celery_app import celery_app


@celery_app.task
def heartbeat() -> str:
    return f"heartbeat:{datetime.utcnow().isoformat()}"
