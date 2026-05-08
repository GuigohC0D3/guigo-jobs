from app.models.job import Job, SearchFilters, SeniorityLevel


def test_job_description_truncated():
    long_desc = "x" * 600
    job = Job(id="1", title="Dev", company="Co", location="Remote", url="https://x.com", description=long_desc)
    assert len(job.description) == 500
    assert job.description.endswith("...")


def test_matches_seniority_junior_blocks_senior():
    filters = SearchFilters(seniority=SeniorityLevel.JUNIOR)
    assert not filters.matches_seniority_keyword("Senior Software Engineer")
    assert filters.matches_seniority_keyword("Junior Backend Developer")
    assert filters.matches_seniority_keyword("Backend Developer")


def test_matches_seniority_any_allows_all():
    filters = SearchFilters(seniority=SeniorityLevel.ANY)
    assert filters.matches_seniority_keyword("Senior Staff Engineer")
    assert filters.matches_seniority_keyword("Junior Frontend Dev")


def test_job_to_dict_serializable():
    from datetime import datetime, timezone
    job = Job(
        id="x1",
        title="Dev",
        company="Co",
        location="Remote",
        url="https://x.com",
        published_at=datetime.now(timezone.utc),
    )
    d = job.to_dict()
    assert isinstance(d["published_at"], str)
    assert "T" in d["published_at"]
