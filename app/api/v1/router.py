from fastapi import APIRouter

from app.api.v1.endpoints import admin, compare, models, prices, providers

api_router = APIRouter(prefix="/v1")
api_router.include_router(models.router)
api_router.include_router(providers.router)
api_router.include_router(prices.router)
api_router.include_router(compare.router)
api_router.include_router(admin.router)
