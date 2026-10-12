# Pretium — Arquitetura

Open API for comparing AI model prices across providers.

## Visão geral

O Pretium ingere preços de modelos de IA de fontes públicas (OpenRouter, LiteLLM), normaliza para um formato interno canônico e expõe via API REST com cache, histórico e comparação.

```
┌────────────┐     ┌─────────┐     ┌───────────┐
│ OpenRouter │────▶│         │     │  Postgres  │
└────────────┘     │ Celery  │───▶ │  (histórico│
┌────────────┐     │ worker  │     │  imutável) │
│  LiteLLM   │────▶│ + Beat  │     └───────────┘
└────────────┘     └────┬────┘
                        │ lock/status
                   ┌────▼────┐
                   │  Redis  │───┐
                   └─────────┘   │
                                 ▼
┌──────┐     ┌─────────────────────────┐
│nginx │────▶│ FastAPI (cache, rate   │
└──────┘     │ limit, métricas, logs) │
             └─────────────────────────┘
```

## Fluxo de ingestão

1. Celery Beat agenda: OpenRouter a cada 30min, LiteLLM a cada 6h
2. `ingest_source(source)`:
   - Adquire lock Redis (`ingest:{source}`) — segunda execução simultânea é rejeitada com `skipped`
   - `adapter.fetch()` — HTTP com retry/backoff (tenacity, 3 tentativas)
   - `adapter.normalize(raw)` — converte para lista de `NormalizedPrice`
   - Payload bruto guardado em `raw_payloads` (JSONB)
   - Para cada preço: quantiza para escala `NUMERIC(20,10)` e compara com o último valor; insere nova linha de histórico **apenas se mudou**
   - Registra `ingestion_runs` com status e contagem de mudanças

### Por que quantizar antes de comparar

A coluna `model_prices.amount` é `NUMERIC(20,10)` — o Postgres arredonda na escrita. Fontes podem enviar mais casas decimais (ex.: `0.00000020988`). Comparar o Decimal cru com o valor arredondado do banco sempre diferiria, duplicando histórico a cada run. O fix: `Decimal(p.amount).quantize(Decimal("0.0000000001"))` antes de comparar.

## Adaptadores

Cada fonte implementa `BaseAdapter` (ABC): `fetch()` com retry + `normalize()` → `list[NormalizedPrice]`.

| Fonte | Arquivo | Particularidade |
|---|---|---|
| OpenRouter | `app/adapters/openrouter.py` | Preços já em USD/1M tokens |
| LiteLLM | `app/adapters/litellm.py` | Preços per-token; multiplica por 1M |

Nova fonte = novo arquivo + registro em `app/adapters/registry.py`.

## Modelo de dados

```
providers 1─N models 1─N model_prices N─1 raw_payloads N─1 ingestion_runs
```

| Tabela | Papel |
|---|---|
| `providers` | Provedores (upsert por slug) |
| `models` | Modelos por provedor (único por `provider_id+external_id`) |
| `model_prices` | **Histórico imutável**: uma linha por mudança de preço (`NUMERIC(20,10)`, Decimal end-to-end) |
| `ingestion_runs` | Auditoria de cada execução |
| `raw_payloads` | Payload bruto JSONB de cada run |

O "preço atual" de um modelo é a linha mais recente por `effective_at` — nunca se atualiza linha existente.

## API

Ver `README.md` para a tabela de endpoints. Camadas de proteção:

- **Cache Redis** com TTL por tipo de endpoint (list 60s / detail 60s / history 300s / compare 120s)
- **Rate limit**: 60 req/min por IP (ou por API key) via middleware; Nginx na frente
- **Admin**: header `X-API-Key` (401 sem key)

## Infra

- Docker Compose: `api`, `worker` (celery worker+beat em um processo, `-B`), `postgres`, `redis`, `nginx`
- Memória total da stack: ~250MB
- Métricas Prometheus em `/metrics` (`pretium_requests_total`, `pretium_request_latency_seconds`, `pretium_ingestion_changes_total`)
- Logs estruturados JSON (structlog)
- Migrações Alembic (`alembic/versions/`)

## Decisões técnicas

| Decisão | Motivo |
|---|---|
| Decimal, nunca float, para preço | Precisão monetária; serializado como string |
| `NUMERIC(20,10)` | Escala suficiente para preços per-token/1M |
| Histórico append-only | Trilha de auditoria de mudanças de preço |
| Lock Redis por fonte | Evita ingestão duplicada concorrente |
| Celery `-B` em um processo | Economiza ~150MB vs worker+beat separados |
| OpenRouter + LiteLLM como fontes primárias | APIs estruturadas; scraping só como último recurso |
