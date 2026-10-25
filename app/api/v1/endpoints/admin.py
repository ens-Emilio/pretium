from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from redis import Redis
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.db import get_db
from app.core.security import require_admin
from app.models import IngestionRun
from app.worker.tasks import sync_source

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)])

_redis = Redis.from_url(get_settings().redis_url, decode_responses=True)


@router.post("/ingestions/{source}")
def trigger_ingestion(source: str) -> dict:
    if source not in ("openrouter", "litellm"):
        raise HTTPException(400, "unknown source")
    task = sync_source.delay(source)
    return {"task_id": task.id, "status": "queued"}


@router.post("/reindex")
def reindex() -> dict:
    """Flush all response caches so the next reads rebuild from the DB."""
    patterns = ("models:*", "model:*", "history:*", "compare:*", "prices_history:*")
    keys: list[str] = []
    for pat in patterns:
        keys.extend(_redis.scan_iter(pat))
    if keys:
        _redis.delete(*keys)
    return {"status": "reindexed", "cache_keys_flushed": len(keys)}


@router.get("/health")
def health(db: Annotated[Session, Depends(get_db)]) -> dict:
    last_runs = db.execute(
        select(IngestionRun).order_by(IngestionRun.started_at.desc()).limit(5)
    ).scalars().all()
    return {
        "status": "ok",
        "recent_runs": [
            {
                "source": r.source,
                "status": r.status,
                "started_at": r.started_at,
                "changes": r.detected_changes,
            }
            for r in last_runs
        ],
    }
