from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any

from app.models.job import Job, SearchFilters
from app.providers.base import BaseProvider


class RemotiveProvider(BaseProvider):
    name = "remotive"
    _BASE_URL = "https://remotive.com/api/remote-jobs"

    def fetch(self, filters: SearchFilters) -> list[Job]:
        params: dict[str, Any] = {"limit": 100}

        search_terms = filters.keywords + filters.technologies
        if search_terms:
            params["search"] = " ".join(search_terms[:3])

        data = self._http.get(self._BASE_URL, params=params)
        if not isinstance(data, dict):
            return []

        raw_jobs = data.get("jobs", [])
        jobs: list[Job] = []

        for item in raw_jobs:
            job = self._parse(item)
            if job and self._matches(job, filters):
                jobs.append(job)

        return jobs[: filters.limit]

    def _parse(self, item: dict[str, Any]) -> Job | None:
        try:
            job_id = str(item.get("id", hashlib.md5(item.get("url", "").encode()).hexdigest()[:12]))
            title = item.get("title", "")
            company = item.get("company_name", "Unknown")
            candidate_region = item.get("candidate_required_location", "Worldwide")
            salary = item.get("salary") or None
            url = item.get("url", "")

            pub_date = None
            if pub_str := item.get("publication_date"):
                try:
                    pub_date = datetime.fromisoformat(pub_str.replace("Z", "+00:00"))
                except ValueError:
                    pass

            tags = item.get("tags") or []

            return Job(
                id=f"remotive_{job_id}",
                title=title,
                company=company,
                location=candidate_region or "Remote",
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

        if filters.max_days_old and job.published_at:
            now = datetime.now(timezone.utc)
            pub = job.published_at
            if pub.tzinfo is None:
                pub = pub.replace(tzinfo=timezone.utc)
            if (now - pub).days > filters.max_days_old:
                return False

        return True
