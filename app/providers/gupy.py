from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any

from app.models.job import ContractType, Job, SearchFilters
from app.providers.base import BaseProvider


_CONTRACT_MAP = {
    "full-time": ContractType.FULL_TIME,
    "part-time": ContractType.PART_TIME,
    "internship": ContractType.INTERNSHIP,
    "freelancer": ContractType.FREELANCE,
}


class GupyProvider(BaseProvider):
    name = "gupy"
    _BASE_URL = "https://portal.api.gupy.io/api/job"

    def fetch(self, filters: SearchFilters) -> list[Job]:
        params: dict[str, Any] = {"limit": min(filters.limit, 100), "offset": 0}

        terms = filters.keywords + filters.technologies
        if terms:
            params["jobName"] = " ".join(terms[:4])

        if filters.remote_only:
            params["isRemoteWork"] = "true"

        data = self._http.get(self._BASE_URL, params=params)
        if not isinstance(data, dict):
            return []

        jobs: list[Job] = []
        for item in data.get("data", []):
            job = self._parse(item)
            if job and self._matches(job, filters):
                jobs.append(job)

        return jobs[: filters.limit]

    def _parse(self, item: dict[str, Any]) -> Job | None:
        try:
            job_id = str(item.get("id") or hashlib.md5(str(item).encode()).hexdigest()[:12])
            title = item.get("name", "")
            company = item.get("careerPageName", "Unknown")

            city = item.get("city") or ""
            state = item.get("state") or ""
            location = ", ".join(filter(None, [city, state, "Brasil"])) or "Brasil"

            remote = bool(item.get("isRemoteWork", False))
            url = item.get("jobUrl", "")

            pub_date = None
            if pub_str := item.get("publishedDate"):
                try:
                    pub_date = datetime.fromisoformat(pub_str.replace("Z", "+00:00"))
                except ValueError:
                    pass

            contract_raw = item.get("type", "")
            contract = _CONTRACT_MAP.get(contract_raw, ContractType.ANY)

            tags: list[str] = []
            if contract_raw:
                tags.append(contract_raw)
            if remote:
                tags.append("remote")

            return Job(
                id=f"gupy_{job_id}",
                title=title,
                company=company,
                location=location,
                remote=remote,
                url=url,
                published_at=pub_date,
                tags=tags,
                contract_type=contract,
                source=self.name,
            )
        except Exception:
            return None

    def _matches(self, job: Job, filters: SearchFilters) -> bool:
        if not filters.matches_seniority_keyword(job.title):
            return False

        if filters.remote_only and not job.remote:
            return False

        if filters.max_days_old and job.published_at:
            now = datetime.now(timezone.utc)
            pub = job.published_at
            if pub.tzinfo is None:
                pub = pub.replace(tzinfo=timezone.utc)
            if (now - pub).days > filters.max_days_old:
                return False

        return True
