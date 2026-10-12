from app.schemas.normalized import NormalizedPrice

from .base import BaseAdapter

# OpenRouter prices are USD per 1M tokens
_OR_UNITS = {
    "prompt": "per_1m_input_tokens",
    "completion": "per_1m_output_tokens",
}


class OpenRouterAdapter(BaseAdapter):
    source = "openrouter"
    url = "https://openrouter.ai/api/v1/models"

    def normalize(self, raw: dict) -> list[NormalizedPrice]:
        out = []
        for m in raw.get("data", []):
            pricing = m.get("pricing", {})
            for field, unit in _OR_UNITS.items():
                amount = pricing.get(field)
                if amount is None or float(amount) < 0:
                    continue
                out.append(
                    NormalizedPrice(
                        external_model_id=m["id"],
                        model_name=m.get("name", m["id"]),
                        provider_slug="openrouter",
                        modality="multimodal" if m.get("architecture", {}).get("modality") else "text",
                        context_window=m.get("context_length", 0) or 0,
                        unit=unit,
                        amount=str(amount),
                    )
                )
        return out
