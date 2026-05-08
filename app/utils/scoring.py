from __future__ import annotations

from datetime import datetime, timezone

from app.core.config import settings
from app.models.job import Job, SearchFilters, SeniorityLevel


def compute_relevance_score(job: Job, filters: SearchFilters) -> float:
    score = 0.0
    title_lower = job.title.lower()
    desc_lower = (job.description or "").lower()
    tags_lower = [t.lower() for t in job.tags]

    for kw in filters.keywords:
        kw_lower = kw.lower()
        if kw_lower in title_lower:
            score += settings.score_keyword_match * 1.5
        elif kw_lower in desc_lower or kw_lower in tags_lower:
            score += settings.score_keyword_match

    for tech in filters.technologies:
        tech_lower = tech.lower()
        if tech_lower in tags_lower:
            score += settings.score_tech_match
        elif tech_lower in title_lower or tech_lower in desc_lower:
            score += settings.score_tech_match * 0.7

    if filters.seniority == SeniorityLevel.JUNIOR:
        junior_hits = {"junior", "jr", "entry", "trainee", "graduate"}
        if any(h in title_lower for h in junior_hits):
            score += settings.score_junior_title

    if job.published_at:
        now = datetime.now(timezone.utc)
        pub = job.published_at
        if pub.tzinfo is None:
            pub = pub.replace(tzinfo=timezone.utc)
        days_old = (now - pub).days
        if days_old <= 3:
            score += settings.score_recent_post * 2
        elif days_old <= 7:
            score += settings.score_recent_post
        elif days_old <= 14:
            score += settings.score_recent_post * 0.5

    if job.salary:
        score += 0.5

    return round(score, 2)


def rank_jobs(jobs: list[Job], filters: SearchFilters) -> list[Job]:
    for job in jobs:
        job.relevance_score = compute_relevance_score(job, filters)
    return sorted(jobs, key=lambda j: j.relevance_score, reverse=True)
