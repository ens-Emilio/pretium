from app.worker import celery_app
from app.worker.ingest import ingest_source


@celery_app.task(name="app.worker.tasks.sync_source")
def sync_source(source: str) -> dict:
    return ingest_source(source)
