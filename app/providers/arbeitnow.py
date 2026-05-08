from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any

from app.models.job import Job, SearchFilters
from app.providers.base import BaseProvider


class ArbeitnowProvider(BaseProvider):
    name = "arbeitnow"
    _BASE_URL = "https://www.arbeitnow.com/api/job-board-api"

    def fetch(self, filters: SearchFilters) -> list[Job]:
        data = self._http.get(self._BASE_URL)
        if not isinstance(data, dict):
            return []

        raw_jobs = data.get("data", [])
        jobs: list[Job] = []

        search_terms = [t.lower() for t in (filters.keywords + filters.technologies)]

        for item in raw_jobs:
            job = self._parse(item)
            if not job:
                continue

            if not filters.matches_seniority_keyword(job.title):
                continue

            if search_terms:
                searchable = (
                    job.title + " " + " ".join(job.tags) + " " + (job.description or "")
                ).lower()
                if not any(t in searchable for t in search_terms):
                    continue

            if not item.get("remote", False) and filters.remote_only:
                continue

            jobs.append(job)

            if len(jobs) >= filters.limit:
                break

        return jobs

    def _parse(self, item: dict[str, Any]) -> Job | None:
        try:
            slug = item.get("slug", "")
            job_id = slug or hashlib.md5(item.get("url", "").encode()).hexdigest()[:12]
            title = item.get("title", "")
            company = item.get("company_name", "Unknown")
            location = item.get("location", "Remote")
            url = item.get("url", "")
            tags = item.get("tags") or []
            remote = item.get("remote", False)

            pub_date = None
            if epoch := item.get("published_at"):
                try:
                    pub_date = datetime.fromtimestamp(int(epoch), tz=timezone.utc)
                except (ValueError, OSError):
                    pass

            return Job(
                id=f"arbeitnow_{job_id}",
                title=title,
                company=company,
                location=location,
                remote=bool(remote),
                url=url,
                published_at=pub_date,
                description=item.get("description"),
                tags=[str(t) for t in tags],
                source=self.name,
            )
        except Exception:
            return None
