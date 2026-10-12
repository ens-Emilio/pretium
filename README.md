# Pretium

Open API for comparing AI model prices across providers.

## Docs
- [ARCHITECTURE.md](ARCHITECTURE.md) — design, data model, ingestion flow
- [OPERATIONS.md](OPERATIONS.md) — VPS deployment and maintenance
- [CONTRIBUTING.md](CONTRIBUTING.md) — setup, conventions, adding sources

## Features
- Real-time price ingestion from OpenRouter and LiteLLM
- Public REST API with filtering, comparison, and history endpoints
- Admin endpoints for triggering ingestion and cache invalidation
- Rate limiting (Nginx + per-key Redis)
- Prometheus metrics
- Structured JSON logs

## Quick Start

```bash
docker compose up -d
```

API available at `http://localhost:8000` (or behind nginx at `http://localhost`).

## Endpoints

### Public (read-only)
| Method | Path | Description |
|---|---|---|
| GET | `/health` | Health check (DB + Redis) |
| GET | `/v1/models` | List models with filters |
| GET | `/v1/models/{id}` | Model details with current prices |
| GET | `/v1/models/{id}/history` | Price history for a model |
| GET | `/v1/providers` | List providers |
| GET | `/v1/prices/history` | Global price history |
| GET | `/v1/compare` | Cheapest models for a unit |

### Admin (requires `X-API-Key`)
| Method | Path | Description |
|---|---|---|
| POST | `/v1/admin/ingestions/{source}` | Trigger ingestion (`openrouter` or `litellm`) |
| POST | `/v1/admin/reindex` | Flush response caches |
| GET | `/v1/admin/health` | Admin health with recent runs |

### Filters (for `/v1/models`)
- `modality` — e.g. `text`, `multimodal`
- `provider` — provider slug
- `min_price` / `max_price` — per 1M input tokens
- `context_min` — minimum context window
- `updated_since` — ISO timestamp

## Deploy

See [OPERATIONS.md](OPERATIONS.md) for VPS deployment (Docker Compose) and maintenance.

## Configuration (env vars)

| Variable | Default | Description |
|---|---|---|
| `PRETIUM_DATABASE_URL` | `postgresql+psycopg://pretium:pretium@postgres:5432/pretium` | PostgreSQL connection |
| `PRETIUM_REDIS_URL` | `redis://redis:6379/0` | Redis connection |
| `PRETIUM_ADMIN_API_KEY` | `change-me` | Admin key (change in production!) |
| `PRETIUM_CACHE_TTL_LIST` | `60` | Models list cache TTL (s) |
| `PRETIUM_CACHE_TTL_DETAIL` | `60` | Model detail cache TTL (s) |
| `PRETIUM_CACHE_TTL_HISTORY` | `300` | History/compare cache TTL (s) |

## Data Sources

Price data provided by:
- [OpenRouter](https://openrouter.ai/) — via public API
- [LiteLLM](https://github.com/BerriAI/litellm) — MIT licensed, via public JSON

## License

Apache-2.0 — see [LICENSE](LICENSE).

## Disclaimer

This service aggregates public pricing data. Prices may be stale; always verify with the provider before making decisions. Not affiliated with OpenRouter, LiteLLM, or any model provider.