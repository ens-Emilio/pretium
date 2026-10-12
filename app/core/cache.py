import json
from typing import Any

import redis

from app.core.config import get_settings

_settings = get_settings()
_client = redis.Redis.from_url(_settings.redis_url, decode_responses=True)


def cache_get_json(key: str) -> Any | None:
    raw: str | None = _client.get(key)  # type: ignore[assignment]
    return json.loads(raw) if raw else None


def cache_set_json(key: str, value: Any, ttl: int) -> None:
    _client.setex(key, ttl, json.dumps(value, default=str))
