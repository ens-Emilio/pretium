from datetime import datetime

from decimal import Decimal

from pydantic import BaseModel, ConfigDict, field_serializer


class ProviderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())

    id: int
    slug: str
    name: str


class PriceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())

    unit: str
    amount: Decimal  # money is Decimal end-to-end, serialized as string
    currency: str
    effective_at: datetime

    @field_serializer("amount")
    def _ser_amount(self, v: Decimal) -> str:
        return format(v.normalize(), "f")


class ModelOut(BaseModel):
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())

    id: int
    provider: ProviderOut
    external_id: str
    name: str
    modality: str
    context_window: int
    prices: list[PriceOut] = []


class HistoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())

    model_id: int
    unit: str
    amount: Decimal
    currency: str
    effective_at: datetime

    @field_serializer("amount")
    def _ser_amount(self, v: Decimal) -> str:
        return format(v.normalize(), "f")


class CompareOut(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    model_id: int
    name: str
    per_1m_input_tokens: str | None = None
    per_1m_output_tokens: str | None = None
