from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Provider(Base):
    __tablename__ = "providers"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(100), unique=True)
    name: Mapped[str] = mapped_column(String(200))
    models: Mapped[list["Model"]] = relationship(back_populates="provider")


class Model(Base):
    __tablename__ = "models"
    __table_args__ = (UniqueConstraint("provider_id", "external_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    provider_id: Mapped[int] = mapped_column(ForeignKey("providers.id"))
    external_id: Mapped[str] = mapped_column(String(255))
    name: Mapped[str] = mapped_column(String(255))
    modality: Mapped[str] = mapped_column(String(50), default="text")
    context_window: Mapped[int] = mapped_column(default=0)

    provider: Mapped[Provider] = relationship(back_populates="models")
    prices: Mapped[list["ModelPrice"]] = relationship(back_populates="model")


class ModelPrice(Base):
    __tablename__ = "model_prices"
    __table_args__ = (
        UniqueConstraint("model_id", "effective_at", "unit"),
        Index("ix_model_prices_model_effective", "model_id", "effective_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    model_id: Mapped[int] = mapped_column(ForeignKey("models.id"))
    unit: Mapped[str] = mapped_column(String(50))
    # NUMERIC(20,10): Decimal in Python, never float for money
    amount: Mapped[float] = mapped_column(Numeric(20, 10))
    currency: Mapped[str] = mapped_column(String(10), default="USD")
    effective_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    raw_payload_id: Mapped[int] = mapped_column(ForeignKey("raw_payloads.id"))
    model: Mapped[Model] = relationship(back_populates="prices")


class IngestionRun(Base):
    __tablename__ = "ingestion_runs"

    id: Mapped[int] = mapped_column(primary_key=True)
    source: Mapped[str] = mapped_column(String(50))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="running")
    detected_changes: Mapped[int] = mapped_column(default=0)


class RawPayload(Base):
    __tablename__ = "raw_payloads"

    id: Mapped[int] = mapped_column(primary_key=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("ingestion_runs.id"))
    payload: Mapped[dict] = mapped_column(JSONB)
