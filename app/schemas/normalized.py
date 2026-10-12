from pydantic import BaseModel, ConfigDict


class NormalizedPrice(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    """Internal canonical price every adapter converts to."""

    external_model_id: str
    model_name: str
    provider_slug: str
    modality: str = "text"
    context_window: int = 0
    unit: str  # e.g. per_1m_input_tokens
    amount: str  # Decimal as string
    currency: str = "USD"
