import time

from fastapi import FastAPI, Request, Response
from redis import Redis
from redis.exceptions import RedisError
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from starlette.middleware.base import BaseHTTPMiddleware

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.db import engine
from app.core.logging import logger
from app.core.metrics import REQUEST_COUNT, REQUEST_LATENCY, metrics_body
from app.core.ratelimit import rate_limit_middleware

app = FastAPI(title="Pretium", version="0.1.0")
app.add_middleware(BaseHTTPMiddleware, dispatch=rate_limit_middleware)
app.include_router(api_router)

_redis = Redis.from_url(get_settings().redis_url, decode_responses=True)


@app.get("/health")
def root_health() -> dict:
    db_ok = False
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        db_ok = True
    except SQLAlchemyError as e:
        logger.error("db_health_failed", error=str(e))
    redis_ok = False
    try:
        redis_ok = bool(_redis.ping())
    except RedisError as e:
        logger.error("redis_health_failed", error=str(e))
    return {"status": "ok" if db_ok and redis_ok else "degraded", "db": db_ok, "redis": redis_ok}


@app.get("/metrics")
def prometheus_metrics() -> Response:
    return Response(content=metrics_body(), media_type="text/plain")


@app.middleware("http")
async def instrument(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    duration = time.perf_counter() - start
    route = request.scope.get("route")
    path = route.path if route else request.url.path
    REQUEST_COUNT.labels(request.method, path, response.status_code).inc()
    REQUEST_LATENCY.labels(request.method, path).observe(duration)
    return response
