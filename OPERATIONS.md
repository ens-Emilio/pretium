# Pretium — Guia de Operação (VPS ShardCloud)

## Estado atual

- VM: `pretium` (`dd8ebd9b-0f3f-43ee-8352-9db2814512c0`), IP `154.29.76.173`, Ubuntu 24.04, 4GB RAM
- Stack: `/opt/pretium/` via Docker Compose
- Contato via API MCP ShardCloud (exec_vm_command)

## Comandos comuns

Todos via SSH na VM ou `exec_vm_command`:

```bash
cd /opt/pretium

# status
docker compose ps

# logs
docker compose logs api --tail 50 -f
docker compose logs worker --tail 50 -f

# reiniciar
docker compose restart api
docker compose up -d --build   # após mudar código

# migration
docker compose exec api alembic upgrade head

# ingestão manual
docker compose exec api python -c \
  "from app.worker.ingest import ingest_source; print(ingest_source('openrouter'))"

# flush de cache
curl -X POST -H "X-API-Key: $KEY" http://localhost/v1/admin/reindex
```

## Variáveis

`PRETIUM_ADMIN_API_KEY` está no `/opt/pretium/docker-compose.yml` (sed inline no deploy).
Para trocar: editar o compose e `docker compose up -d api`.

## Rotinas automáticas

- OpenRouter: a cada 30min (Celery Beat)
- LiteLLM: a cada 6h
- Lock Redis evita runs duplicados

## Backup

`pgdata` é volume Docker nomeado. Para backup manual:

```bash
docker compose exec postgres pg_dump -U pretium pretium > backup.sql
```

A ShardCloud também oferece `create_backup` / `update_autobackup` via API MCP.

## Saúde

- `GET /health` — status DB + Redis
- `GET /metrics` — Prometheus
- `GET /v1/admin/health` — últimos runs de ingestão (com API key)

## Deploy de código novo

```bash
# local: empacotar
tar czf /tmp/pretium.tar.gz --exclude='.venv' --exclude='__pycache__' \
  --exclude='.git' --exclude='.mypy_cache' --exclude='*.pyc' \
  --exclude='.pytest_cache' --exclude='.ruff_cache' .

# transferir (via exec_vm_command: base64 -> /opt/pretium/project.tar.gz)
# na VM:
cd /opt/pretium && tar xzf project.tar.gz
docker compose up -d --build
docker compose exec api alembic upgrade head
```
