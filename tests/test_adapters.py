from app.adapters.litellm import LiteLLMAdapter
from app.adapters.openrouter import OpenRouterAdapter

OR_SAMPLE = {
    "data": [
        {
            "id": "test/model",
            "name": "Test Model",
            "context_length": 128000,
            "architecture": {"modality": "text+image->text"},
            "pricing": {"prompt": "0.001", "completion": "0.002"},
        },
        {"id": "neg/model", "name": "Neg", "pricing": {"prompt": "-1"}},
    ]
}

LITELLM_SAMPLE = {
    "example_model_name": {"input_cost_per_token": 9.99},
    "gpt/test": {
        "litellm_provider": "openai/gpt-test",
        "max_input_tokens": 1000,
        "mode": "chat",
        "input_cost_per_token": 0.000001,
        "output_cost_per_token": 0.000002,
    },
}

def test_openrouter_normalize():
    prices = OpenRouterAdapter().normalize(OR_SAMPLE)
    units = {(p.external_model_id, p.unit, p.amount) for p in prices}
    assert ("test/model", "per_1m_input_tokens", "0.001") in units
    assert ("test/model", "per_1m_output_tokens", "0.002") in units
    assert all("neg" not in p.external_model_id for p in prices)


def test_litellm_normalize_per_million():
    prices = LiteLLMAdapter().normalize(LITELLM_SAMPLE)
    by_unit = {p.unit: p.amount for p in prices}
    assert by_unit["per_1m_input_tokens"] == "1.0"
    assert by_unit["per_1m_output_tokens"] == "2.0"
    assert all(p.external_model_id != "example_model_name" for p in prices)
    assert prices[0].provider_slug == "openai"


if __name__ == "__main__":
    test_openrouter_normalize()
    test_litellm_normalize_per_million()
    print("ADAPTER_TESTS_OK")
