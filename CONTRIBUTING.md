# Contribuindo com o Pretium

## Setup

```bash
uv venv && uv pip install -r requirements.txt --python .venv/bin/python
docker compose up -d postgres redis
alembic upgrade head
uvicorn app.main:app --reload
```

## Antes de abrir PR

```bash
ruff check app tests
mypy app --ignore-missing-imports
pytest -q
```

## Adicionando uma fonte de preços

1. Crie `app/adapters/<fonte>.py` herdando de `BaseAdapter`
2. Implemente `normalize()` retornando `list[NormalizedPrice]` (preços per-1M-tokens como string Decimal)
3. Registre em `app/adapters/registry.py`
4. Adicione teste de normalização em `tests/test_adapters.py`
5. Agende no beat (`app/worker/__init__.py`) se for periódica

## Convenções

- Preço é sempre `Decimal`/`NUMERIC(20,10)` — nunca float
- Histórico é append-only: nunca UPDATE em `model_prices`
- Ingestão deve ser idempotente (compare quantizado com o último valor)
