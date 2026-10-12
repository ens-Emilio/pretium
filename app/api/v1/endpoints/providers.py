from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models import Provider
from app.schemas import ProviderOut

router = APIRouter(prefix="/providers", tags=["providers"])


@router.get("", response_model=list[ProviderOut])
def list_providers(db: Session = Depends(get_db)):
    return db.execute(select(Provider)).scalars().all()
