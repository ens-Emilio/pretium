from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.cache import cache_get_json, cache_set_json
from app.core.config import get_settings
from app.core.db import get_db
from app.models import Model, ModelPrice
from app.schemas import CompareOut

router = APIRouter(tags=["compare"])
settings = get_settings()


@router.get("/compare", response_model=list[CompareOut])
def compare(
    unit: str = "per_1m_input_tokens",
    modality: str | None = None,
    provider: str | None = None,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    """Latest price per model for a unit, cheapest first."""
    cache_key = f"compare:{unit}:{modality}:{provider}:{limit}"
    if cached := cache_get_json(cache_key):
        return cached

    q = (
        select(Model, ModelPrice)
        .join(ModelPrice, ModelPrice.model_id == Model.id)
        .where(ModelPrice.unit == unit)
        .order_by(ModelPrice.amount)
        .limit(limit)
    )
    if modality:
        q = q.where(Model.modality == modality)

    rows = db.execute(q).all()
    out = []
    seen: set[int] = set()
    for model, price in rows:
        if model.id in seen:
            continue
        seen.add(model.id)
        out.append(
            CompareOut(
                model_id=model.id,
                name=model.name,
                per_1m_input_tokens=format(price.amount.normalize(), "f") if unit == "per_1m_input_tokens" else None,
                per_1m_output_tokens=format(price.amount.normalize(), "f") if unit == "per_1m_output_tokens" else None,
            ).model_dump(mode="json")
        )
    cache_set_json(cache_key, out, 120)
    return out
