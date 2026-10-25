from typing import ClassVar

from app.schemas.normalized import NormalizedPrice

from .base import BaseAdapter


class LiteLLMAdapter(BaseAdapter):
    source = "litellm"
    url = "https://raw.githubusercontent.com/BerriAI/litellm/main/model_prices_and_context_window.json"

    _UNITS: ClassVar[dict[str, str]] = {
        "input_cost_per_token": "per_1m_input_tokens",
        "output_cost_per_token": "per_1m_output_tokens",
    }

    def normalize(self, raw: dict) -> list[NormalizedPrice]:
        out = []
        for model_id, m in raw.items():
            if model_id in ("example_model_name",):
                continue
            if not isinstance(m, dict):
                continue
            provider = m.get("litellm_provider", "unknown").split("/")[0]
            for field, unit in self._UNITS.items():
                amount = m.get(field)
                if not amount or amount <= 0:
                    continue
                # litellm gives per-token; normalize to per 1M
                out.append(
                    NormalizedPrice(
                        external_model_id=model_id,
                        model_name=model_id,
                        provider_slug=provider,
                        modality=m.get("mode", "text"),
                        context_window=m.get("max_input_tokens", 0) or 0,
                        unit=unit,
                        amount=str(amount * 1_000_000),
                    )
                )
        return out
