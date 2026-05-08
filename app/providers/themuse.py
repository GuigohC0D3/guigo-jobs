from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any, Optional

from app.core.config import settings
from app.models.job import Job, SearchFilters, SeniorityLevel
from app.providers.base import BaseProvider


_LEVEL_MAP = {
    SeniorityLevel.JUNIOR: ["Entry Level", "Internship"],
    SeniorityLevel.MID: ["Mid Level"],
    SeniorityLevel.SENIOR: ["Senior Level", "Management", "Executive"],
}


class TheMuseProvider(BaseProvider):
    name = "themuse"
    _BASE_URL = "https://www.themuse.com/api/public/jobs"

    def fetch(self, filters: SearchFilters) -> list[Job]:
        params: dict[str, Any] = {
            "page": 0,
            "descending": "true",
        }

        if settings.themuse_api_key:
            params["api_key"] = settings.themuse_api_key

        levels = _LEVEL_MAP.get(filters.seniority)
        if levels:
            params["level"] = levels[0]

        search_terms = filters.keywords + filters.technologies
        if search_terms:
            params["category"] = search_terms[0]

        data = self._http.get(self._BASE_URL, params=params)
        if not isinstance(data, dict):
            return []

        raw_jobs = data.get("results", [])
        jobs: list[Job] = []

        for item in raw_jobs:
            job = self._parse(item)
            if job and self._matches(job, filters):
                jobs.append(job)
                if len(jobs) >= filters.limit:
                    break

        return jobs

    def _parse(self, item: dict[str, Any]) -> Optional[Job]:
        try:
            job_id = str(item.get("id", hashlib.md5(str(item).encode()).hexdigest()[:12]))
            title = item.get("name", "")
            company = item.get("company", {}).get("name", "Unknown")

            locations = item.get("locations", [])
            location = locations[0].get("name", "Remote") if locations else "Remote"
            is_remote = any("remote" in loc.get("name", "").lower() for loc in locations) or not locations

            refs = item.get("refs", {})
            url = refs.get("landing_page", "")

            pub_date = None
            if pub_str := item.get("publication_date"):
                try:
                    pub_date = datetime.fromisoformat(pub_str.replace("Z", "+00:00"))
                except ValueError:
                    pass

            categories = [c.get("name", "") for c in item.get("categories", [])]

            return Job(
                id=f"themuse_{job_id}",
                title=title,
                company=company,
                location=location,
                remote=is_remote,
                url=url,
                published_at=pub_date,
                tags=categories,
                source=self.name,
            )
        except Exception:
            return None

    def _matches(self, job: Job, filters: SearchFilters) -> bool:
        if filters.remote_only and not job.remote:
            return False

        if not filters.matches_seniority_keyword(job.title):
            return False

        all_terms = filters.keywords + filters.technologies
        if all_terms:
            searchable = (job.title + " " + " ".join(job.tags)).lower()
            if not any(t.lower() in searchable for t in all_terms):
                return False

        return True
