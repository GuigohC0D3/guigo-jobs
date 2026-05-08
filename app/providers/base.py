from __future__ import annotations

from abc import ABC, abstractmethod

from app.models.job import Job, SearchFilters
from app.utils.cache import FileCache
from app.utils.http import http_client


class BaseProvider(ABC):
    name: str = "base"
    enabled: bool = True

    def __init__(self) -> None:
        self._cache = FileCache(namespace=self.name)
        self._http = http_client

    @abstractmethod
    def fetch(self, filters: SearchFilters) -> list[Job]:
        ...

    def _cache_key(self, filters: SearchFilters) -> str:
        parts = sorted(filters.keywords + filters.technologies)
        return f"{self.name}:{':'.join(parts)}:{filters.seniority}:{filters.country or 'any'}"

    def search(self, filters: SearchFilters) -> list[Job]:
        if not self.enabled:
            return []

        cache_key = self._cache_key(filters)
        cached = self._cache.get(cache_key)
        if cached is not None:
            from app.models.job import Job as JobModel
            return [JobModel(**j) for j in cached]

        try:
            jobs = self.fetch(filters)
            self._cache.set(cache_key, [j.to_dict() for j in jobs])
            return jobs
        except Exception as e:
            from app.core.logger import logger
            logger.error(f"[{self.name}] fetch failed: {e}")
            return []
