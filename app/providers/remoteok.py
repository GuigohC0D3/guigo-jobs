from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any

from app.models.job import ContractType, Job, SearchFilters, SeniorityLevel
from app.providers.base import BaseProvider


class RemoteOKProvider(BaseProvider):
    name = "remoteok"
    _BASE_URL = "https://remoteok.com/api"

    def fetch(self, filters: SearchFilters) -> list[Job]:
        data = self._http.get(self._BASE_URL, headers={"Accept": "application/json"})
        if not isinstance(data, list):
            return []

        jobs: list[Job] = []
        for item in data:
            if not isinstance(item, dict) or "position" not in item:
                continue

            job = self._parse(item)
            if job and self._matches(job, filters):
                jobs.append(job)

        return jobs[: filters.limit]

    def _parse(self, item: dict[str, Any]) -> Job | None:
        try:
            title = item.get("position", "")
            company = item.get("company", "Unknown")
            tags = item.get("tags") or []
            url = item.get("url") or item.get("apply_url", "")
            salary_min = item.get("salary_min")
            salary_max = item.get("salary_max")
            salary = None
            if salary_min and salary_max:
                salary = f"${salary_min:,} – ${salary_max:,}/yr"
            elif salary_min:
                salary = f"${salary_min:,}+/yr"

            pub_date = None
            if epoch := item.get("epoch"):
                pub_date = datetime.fromtimestamp(int(epoch), tz=timezone.utc)

            job_id = str(item.get("id") or hashlib.md5(url.encode()).hexdigest()[:12])

            return Job(
                id=f"remoteok_{job_id}",
                title=title,
                company=company,
                location="Remote",
                remote=True,
                salary=salary,
                url=url,
                published_at=pub_date,
                description=item.get("description"),
                tags=[str(t) for t in tags],
                source=self.name,
            )
        except Exception:
            return None

    def _matches(self, job: Job, filters: SearchFilters) -> bool:
        if not filters.matches_seniority_keyword(job.title):
            return False

        all_terms = filters.keywords + filters.technologies
        if all_terms:
            searchable = (job.title + " " + " ".join(job.tags) + " " + (job.description or "")).lower()
            if not any(t.lower() in searchable for t in all_terms):
                return False

        if filters.max_days_old and job.published_at:
            now = datetime.now(timezone.utc)
            pub = job.published_at
            if pub.tzinfo is None:
                pub = pub.replace(tzinfo=timezone.utc)
            if (now - pub).days > filters.max_days_old:
                return False

        return True
