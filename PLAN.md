# Plano de Implementação - Pretium

## Visão Geral
Projeto para comparação de preços de modelos de IA usando a stack recomendada:
- Python 3.12+, FastAPI, Pydantic v2
- SQLAlchemy 2, Alembic, PostgreSQL 16/17
- Redis 7, Celery + Celery Beat
- Docker Compose, Nginx, Let's Encrypt
- GitHub Actions, Ruff, pytest

## Fases
1. MVP funcional (FastAPI, PostgreSQL, SQLAlchemy, Redis, Celery básico)
2. Fase robusta (Celery + Beat, métricas, logs, autenticação)

## Estrutura de Pastas
```
pretium/
├── app/
│   ├── api/
│   │   ├── deps.py
│   │   ├── v1/
│   │   │   ├── endpoints/
│   │   │   │   ├── models.py
│   │   │   │   ├── providers.py
│   │   │   │   ├── prices.py
│   │   │   │   ├── compare.py
│   │   │   │   └── admin.py
│   │   │   └── router.py
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   ├── security.py
│   │   │   └── utils.py
│   │   ├── adapters/
│   │   │   ├── base.py
│   │   │   ├── openrouter.py
│   │   │   ├── litellm.py
│   │   │   └── registry.py
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── provider.py
│   │   │   ├── model.py
│   │   │   ├── model_price.py
│   │   │   └── ingestion_run.py
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   ├── model.py
│   │   │   ├── provider.py
│   │   │   ├── price.py
│   │   │   └── comparison.py
│   │   ├── worker/
│   │   │   ├── __init__.py
│   │   │   ├── tasks.py
│   │   │   └── scheduler.py
│   └── main.py
├── alembic/
├── tests/
├── docker/
│   ├── nginx/
│   └── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## Próximos Passos
1. Criar estrutura de diretórios
2. Configurar Docker Compose
3. Implementar modelos SQLAlchemy
4. Criar endpoints de leitura
5. Implementar workers de ingestão
6. Adicionar autenticação e rate limiting
7. Configurar métricas e logs
8. Preparar CI/CD
