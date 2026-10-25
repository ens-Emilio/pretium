from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.cache import cache_get_json, cache_set_json
from app.core.config import get_settings
from app.core.db import get_db
from app.models import ModelPrice
from app.schemas import HistoryOut

router = APIRouter(prefix="/prices", tags=["prices"])
settings = get_settings()


@router.get("/history", response_model=list[HistoryOut])
def price_history(
    db: Annotated[Session, Depends(get_db)],
    since: datetime | None = None,
    limit: int = Query(default=100, le=1000),
):
    """Global price history across all models, newest first."""
    cache_key = f"prices_history:{since}:{limit}"
    if cached := cache_get_json(cache_key):
        return cached
    q = select(ModelPrice).order_by(ModelPrice.effective_at.desc()).limit(limit)
    if since:
        q = q.where(ModelPrice.effective_at >= since)
    rows = db.execute(q).scalars().all()
    result = [HistoryOut.model_validate(r).model_dump(mode="json") for r in rows]
    cache_set_json(cache_key, result, settings.cache_ttl_history)
    return result
