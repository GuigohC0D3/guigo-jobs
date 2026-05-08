from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed

from app.models.job import Job, SearchFilters
from app.providers.base import BaseProvider
from app.providers.registry import get_active_providers
from app.utils.scoring import rank_jobs


class SearchService:
    def __init__(self, providers: list[BaseProvider] | None = None) -> None:
        self._providers = providers or get_active_providers()

    def search(self, filters: SearchFilters) -> list[Job]:
        all_jobs: list[Job] = []
        seen_ids: set[str] = set()

        with ThreadPoolExecutor(max_workers=len(self._providers)) as pool:
            futures = {pool.submit(p.search, filters): p.name for p in self._providers}
            for future in as_completed(futures):
                provider_name = futures[future]
                try:
                    jobs = future.result()
                    for job in jobs:
                        if job.id not in seen_ids:
                            seen_ids.add(job.id)
                            all_jobs.append(job)
                except Exception as e:
                    from app.core.logger import logger
                    logger.error(f"Provider {provider_name} raised: {e}")

        return rank_jobs(all_jobs, filters)

    def search_with_progress(
        self,
        filters: SearchFilters,
        on_provider_done: callable | None = None,
    ) -> list[Job]:
        all_jobs: list[Job] = []
        seen_ids: set[str] = set()

        with ThreadPoolExecutor(max_workers=len(self._providers)) as pool:
            futures = {pool.submit(p.search, filters): p for p in self._providers}
            for future in as_completed(futures):
                provider = futures[future]
                try:
                    jobs = future.result()
                    new_jobs = [j for j in jobs if j.id not in seen_ids]
                    for job in new_jobs:
                        seen_ids.add(job.id)
                        all_jobs.append(job)
                    if on_provider_done:
                        on_provider_done(provider.name, len(new_jobs))
                except Exception as e:
                    from app.core.logger import logger
                    logger.error(f"Provider {provider.name} raised: {e}")
                    if on_provider_done:
                        on_provider_done(provider.name, 0)

        return rank_jobs(all_jobs, filters)
