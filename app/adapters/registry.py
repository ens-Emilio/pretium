from .base import BaseAdapter
from .litellm import LiteLLMAdapter
from .openrouter import OpenRouterAdapter

ADAPTERS: dict[str, BaseAdapter] = {
    a.source: a for a in (OpenRouterAdapter(), LiteLLMAdapter())
}
