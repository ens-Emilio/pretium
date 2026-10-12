from abc import ABC, abstractmethod

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from app.schemas.normalized import NormalizedPrice


class BaseAdapter(ABC):
    source: str
    url: str

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=30))
    def fetch(self) -> dict:
        resp = httpx.get(self.url, timeout=30, headers={"User-Agent": "Pretium/0.1"})
        resp.raise_for_status()
        return resp.json()

    @abstractmethod
    def normalize(self, raw: dict) -> list[NormalizedPrice]:
        ...
