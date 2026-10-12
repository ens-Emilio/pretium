from datetime import UTC, datetime
from decimal import Decimal

import redis
from app.adapters.registry import ADAPTERS
from app.core.config import get_settings
from app.core.logging import logger
from app.core.metrics import INGESTION_CHANGES
from app.core.security import utcnow
from app.core.db import SessionLocal
from app.models import IngestionRun, Model, ModelPrice, Provider, RawPayload

_redis = redis.Redis.from_url(get_settings().redis_url, decode_responses=True)


def _upsert_provider(db, slug: str) -> Provider:
    provider = db.query(Provider).filter_by(slug=slug).first()
    if not provider:
        provider = Provider(slug=slug, name=slug)
        db.add(provider)
        db.flush()
    return provider


def _upsert_model(db, provider: Provider, external_id: str, name: str, modality: str, context: int) -> Model:
    model = (
        db.query(Model)
        .filter_by(provider_id=provider.id, external_id=external_id)
        .first()
    )
    if not model:
        model = Model(
            provider_id=provider.id,
            external_id=external_id,
            name=name,
            modality=modality,
            context_window=context,
        )
        db.add(model)
        db.flush()
    return model


def ingest_source(source: str) -> dict:
    adapter = ADAPTERS[source]
    lock = _redis.lock(f"ingest:{source}", timeout=600)
    if not lock.acquire(blocking=False):
        return {"source": source, "changes": 0, "skipped": "ingestion already running"}
    db = SessionLocal()
    run = IngestionRun(source=source, started_at=utcnow(), status="running")
    db.add(run)
    db.flush()

    try:
        raw = adapter.fetch()
        payload_row = RawPayload(run_id=run.id, payload=raw)
        db.add(payload_row)
        db.flush()

        prices = adapter.normalize(raw)
        now = utcnow()
        changes = 0
        raw_payload_id = payload_row.id
        for p in prices:
            provider = _upsert_provider(db, p.provider_slug)
            model = _upsert_model(
                db, provider, p.external_model_id, p.model_name, p.modality, p.context_window
            )
            latest = (
                db.query(ModelPrice)
                .filter_by(model_id=model.id, unit=p.unit)
                .order_by(ModelPrice.effective_at.desc())
                .first()
            )
            # quantize to NUMERIC(20,10) scale: the DB rounds on write,
            # so compare at the same scale the column stores
            amount = Decimal(p.amount).quantize(Decimal("0.0000000001"))
            if latest and latest.amount == amount:
                continue  # unchanged, no new history row
            db.add(
                ModelPrice(
                    model_id=model.id,
                    unit=p.unit,
                    amount=amount,
                    currency=p.currency,
                    effective_at=now,
                    raw_payload_id=raw_payload_id,
                )
            )
            changes += 1

        run.status = "success"
        run.detected_changes = changes
        run.finished_at = datetime.now(UTC)
        db.commit()
        INGESTION_CHANGES.labels(source=source).inc(changes)
        logger.info("ingestion_done", source=source, changes=changes, prices_seen=len(prices))
        return {"source": source, "changes": changes}
    except Exception as e:
        db.rollback()
        run.status = "failed"
        db.commit()
        logger.error("ingestion_failed", source=source, error=str(e))
        raise
    finally:
        lock.release()
