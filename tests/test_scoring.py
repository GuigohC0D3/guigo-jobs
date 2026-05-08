from datetime import datetime, timezone

import pytest

from app.models.job import Job, SearchFilters, SeniorityLevel
from app.utils.scoring import compute_relevance_score, rank_jobs


def make_job(**kwargs) -> Job:
    defaults = dict(
        id="test_1",
        title="Junior Python Developer",
        company="Acme",
        location="Remote",
        url="https://example.com/job/1",
        source="test",
        tags=["python", "django"],
    )
    defaults.update(kwargs)
    return Job(**defaults)


def test_keyword_match_boosts_score():
    job = make_job(title="Junior Python Backend Developer")
    filters = SearchFilters(keywords=["python"], seniority=SeniorityLevel.JUNIOR)
    score = compute_relevance_score(job, filters)
    assert score > 0


def test_tech_match_in_tags():
    job = make_job(tags=["react", "typescript", "node"])
    filters = SearchFilters(technologies=["react"], seniority=SeniorityLevel.ANY)
    score = compute_relevance_score(job, filters)
    assert score >= 3.0


def test_senior_title_returns_low_score_for_junior_filter():
    senior_job = make_job(title="Senior Software Engineer", tags=[])
    filters = SearchFilters(keywords=["python"], seniority=SeniorityLevel.JUNIOR)
    score = compute_relevance_score(senior_job, filters)
    assert score == pytest.approx(0.0, abs=1.0)


def test_recent_job_gets_bonus():
    recent_job = make_job(published_at=datetime.now(timezone.utc))
    old_job = make_job(id="test_2", published_at=datetime(2020, 1, 1, tzinfo=timezone.utc))
    filters = SearchFilters(seniority=SeniorityLevel.ANY)
    recent_score = compute_relevance_score(recent_job, filters)
    old_score = compute_relevance_score(old_job, filters)
    assert recent_score > old_score


def test_rank_jobs_returns_sorted():
    jobs = [
        make_job(id="1", title="Backend Dev", tags=[]),
        make_job(id="2", title="Junior Python Engineer", tags=["python", "fastapi"]),
        make_job(id="3", title="Junior React Dev", tags=["react"]),
    ]
    filters = SearchFilters(keywords=["python"], technologies=["fastapi"], seniority=SeniorityLevel.JUNIOR)
    ranked = rank_jobs(jobs, filters)
    assert ranked[0].id == "2"
