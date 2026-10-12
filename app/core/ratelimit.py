import time

from fastapi import Request
from fastapi.responses import JSONResponse
from redis import Redis

from app.core.config import get_settings

_settings = get_settings()
_redis = Redis.from_url(_settings.redis_url, decode_responses=True)

# ponytail: fixed windows; sliding window if abuse patterns demand it
RATE_LIMIT = 60  # requests per window per key
WINDOW = 60  # seconds


async def rate_limit_middleware(request: Request, call_next):
    key = f"ratelimit:{request.client.host if request.client else 'unknown'}"
    if api_key := request.headers.get("X-API-Key"):
        key = f"ratelimit:key:{api_key}"
    count = _redis.incr(key)  # type: ignore[operator]
    if count == 1:
        _redis.expire(key, WINDOW)
    if count > RATE_LIMIT:  # type: ignore[operator]
        return JSONResponse({"detail": "rate limit exceeded"}, status_code=429)
    start = time.perf_counter()
    response = await call_next(request)
    duration = time.perf_counter() - start
    response.headers["X-RateLimit-Limit"] = str(RATE_LIMIT)
    response.headers["X-RateLimit-Remaining"] = str(max(0, RATE_LIMIT - count))  # type: ignore[operator]
    response.headers["X-Process-Time-Ms"] = f"{duration * 1000:.1f}"
    return response
