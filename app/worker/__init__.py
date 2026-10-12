from celery import Celery
from celery.schedules import crontab

from app.core.config import get_settings

settings = get_settings()
celery_app = Celery("pretium", broker=settings.redis_url, backend=settings.redis_url)

celery_app.conf.beat_schedule = {
    "sync-openrouter": {
        "task": "app.worker.tasks.sync_source",
        "schedule": 30 * 60,
        "args": ("openrouter",),
    },
    "sync-litellm": {
        "task": "app.worker.tasks.sync_source",
        "schedule": crontab(hour="*/6", minute=0),
        "args": ("litellm",),
    },
}
