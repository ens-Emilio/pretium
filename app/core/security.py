from datetime import UTC, datetime

from argon2 import PasswordHasher
from fastapi import Header, HTTPException, status

from app.core.config import get_settings

_hasher = PasswordHasher()


def hash_key(raw: str) -> str:
    return _hasher.hash(raw)


def verify_key(raw: str, hashed: str) -> bool:
    try:
        return _hasher.verify(hashed, raw)
    except Exception:
        return False

def require_admin(x_api_key: str | None = Header(alias="X-API-Key", default=None)) -> None:
    # ponytail: single admin key; per-key table if multiple admins needed
    if x_api_key != get_settings().admin_api_key:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "invalid API key")


def utcnow() -> datetime:
    return datetime.now(UTC)
