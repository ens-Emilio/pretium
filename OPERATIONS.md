# Pretium — Operação em produção

## Estado atual

O serviço em produção roda na VPS Contabo e é acessado internamente pela API
Pretium e pelo worker Celery. A VM antiga da ShardCloud foi esvaziada e mantida
ligada como rollback; ela não hospeda mais esta aplicação.

## Configuração

O deploy de produção usa os arquivos privados da VPS. Nunca grave tokens,
senhas ou chaves no `docker-compose.yml`, neste documento ou no Git.

| Variável | Uso |
|---|---|
| `PRETIUM_ADMIN_API_KEY` | Autenticação das rotas `/v1/admin/*` |
| `POSTGRES_PASSWORD` | Senha do PostgreSQL; usada pelo Compose e pela API |
| `PRETIUM_DATABASE_URL` | Conexão PostgreSQL montada pelo Compose |
| `PRETIUM_REDIS_URL` | Broker e cache Redis |

Para gerar uma chave administrativa:

```bash
openssl rand -hex 32
```

Mantenha o `.env` fora do Git e com modo `0600`.

## Comandos

```bash
docker compose ps
docker compose logs api --tail 50
docker compose logs worker --tail 50
docker compose logs beat --tail 50
```

Após código novo ou migrations:

```bash
docker compose up -d --build
docker compose exec api alembic upgrade head
```

Ingestão manual:

```bash
docker compose exec api python -c \
  "from app.worker.ingest import ingest_source; print(ingest_source('openrouter'))"
```

Invalidar cache (substitua a variável pelo segredo do ambiente):

```bash
curl -X POST -H "X-API-Key: $PRETIUM_ADMIN_API_KEY" \
  http://127.0.0.1:8080/v1/admin/reindex
```

## Agendamento

- OpenRouter: a cada 30 minutos pelo Celery Beat.
- LiteLLM: a cada 6 horas.
- O lock no Redis impede duas execuções simultâneas da mesma fonte.

Em produção, execute o worker com `--include=app.worker.tasks`; sem isso o
worker inicia mas não registra a task `app.worker.tasks.sync_source`.

## Saúde e observabilidade

- `GET /health`: banco e Redis.
- `GET /v1/admin/health`: últimos runs de ingestão; exige `X-API-Key`.
- `GET /metrics`: métricas Prometheus.

Exponha `/metrics` apenas na rede interna ou por túnel SSH. Ele não deve ser
publicado sem autenticação ou filtro de borda.

## Backup e restore

Exporte o PostgreSQL periodicamente com formato customizado:

```bash
docker compose exec -T postgres pg_dump -U pretium -Fc pretium > pretium.dump
```

Teste a restauração em um banco temporário antes de confiar no backup. O backup
offsite deve ser criptografado; mantenha a chave de restauração fora do host.

## Segurança de rede

O Compose de desenvolvimento publica apenas o Nginx em `127.0.0.1:8080`.
PostgreSQL, Redis e a API usam portas internas. Em produção, o proxy externo
deve encaminhar para o Nginx ou para a porta interna da API, com TLS e limites
de acesso.

## Separação de dados

Não compartilhe o banco `pretium` com o CRM, SDR, Helio ou outros produtos sem
uma migração explícita e um plano de rollback.