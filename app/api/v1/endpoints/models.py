from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.cache import cache_get_json, cache_set_json
from app.core.config import get_settings
from app.core.db import get_db
from app.models import Model, ModelPrice, Provider
from app.schemas import HistoryOut, ModelOut, PriceOut

router = APIRouter(prefix="/models", tags=["models"])
settings = get_settings()


@router.get("", response_model=list[ModelOut])
def list_models(
    modality: str | None = None,
    provider: str | None = None,
    min_price: float | None = None,
    max_price: float | None = None,
    context_min: int | None = None,
    updated_since: datetime | None = None,
    db: Session = Depends(get_db),
):
    cache_key = f"models:{modality}:{provider}:{min_price}:{max_price}:{context_min}:{updated_since}"
    if cached := cache_get_json(cache_key):
        return cached

    q = (
        select(Model)
        .options(joinedload(Model.provider), joinedload(Model.prices))
    )
    if provider:
        q = q.join(Provider, Model.provider_id == Provider.id).where(Provider.slug == provider)
    if modality:
        q = q.where(Model.modality == modality)
    if context_min:
        q = q.where(Model.context_window >= context_min)
    if updated_since:
        q = q.join(ModelPrice).where(ModelPrice.effective_at >= updated_since).distinct()
    models = db.execute(q).unique().scalars().all()

    result = [
        ModelOut.model_validate(m).model_dump(mode="json")
        for m in models
        if _price_filter(m, min_price, max_price)
    ]
    cache_set_json(cache_key, result, settings.cache_ttl_list)
    return result


def _price_filter(m: Model, min_price: float | None, max_price: float | None) -> bool:
    if min_price is None and max_price is None:
        return True
    input_price = next(
        (float(p.amount) for p in m.prices if p.unit == "per_1m_input_tokens"), None
    )
    if min_price is not None and (input_price is None or input_price < min_price):
        return False
    if max_price is not None and (input_price is None or input_price > max_price):
        return False
    return True


@router.get("/{model_id}", response_model=ModelOut)
def get_model(model_id: int, db: Session = Depends(get_db)):
    cache_key = f"model:{model_id}"
    if cached := cache_get_json(cache_key):
        return cached
    m = db.get(Model, model_id)
    if not m:
        raise HTTPException(404, "model not found")
    result = ModelOut.model_validate(m).model_dump(mode="json")
    cache_set_json(cache_key, result, settings.cache_ttl_detail)
    return result


@router.get("/{model_id}/history", response_model=list[HistoryOut])
def model_history(model_id: int, db: Session = Depends(get_db)):
    cache_key = f"history:{model_id}"
    if cached := cache_get_json(cache_key):
        return cached
    rows = (
        db.execute(
            select(ModelPrice).where(ModelPrice.model_id == model_id).order_by(ModelPrice.effective_at)
        )
        .scalars()
        .all()
    )
    result = [HistoryOut.model_validate(r).model_dump(mode="json") for r in rows]
    cache_set_json(cache_key, result, settings.cache_ttl_history)
    return result


@router.get("/{model_id}/prices", response_model=list[PriceOut])
def model_prices(model_id: int, db: Session = Depends(get_db)):
    return (
        db.execute(select(ModelPrice).where(ModelPrice.model_id == model_id))
        .scalars()
        .all()
    )
