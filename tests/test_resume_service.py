from __future__ import annotations

from pathlib import Path

import pytest

from app.models.job import Job, SeniorityLevel
from app.services.resume import ResumeData, ResumeService


@pytest.fixture
def svc() -> ResumeService:
    return ResumeService()


class TestExtractTechnologies:
    def test_finds_python_and_fastapi(self, svc):
        result = svc._extract_technologies("I work with Python and FastAPI daily.")
        assert "python" in result
        assert "fastapi" in result

    def test_case_insensitive(self, svc):
        result = svc._extract_technologies("REACT developer with TypeScript")
        assert "react" in result
        assert "typescript" in result

    def test_partial_word_not_matched(self, svc):
        # "javalanche" should NOT match "java"
        result = svc._extract_technologies("javalanche processing system")
        assert "java" not in result

    def test_unknown_term_not_included(self, svc):
        result = svc._extract_technologies("I like cooking and hiking")
        assert result == []

    def test_returns_sorted_list(self, svc):
        result = svc._extract_technologies("Python and AWS and Docker")
        assert result == sorted(result)


class TestExtractSeniority:
    def test_detects_senior(self, svc):
        assert svc._extract_seniority("Senior Software Engineer") == SeniorityLevel.SENIOR

    def test_detects_lead(self, svc):
        assert svc._extract_seniority("Lead Developer at Acme") == SeniorityLevel.SENIOR

    def test_detects_junior(self, svc):
        assert svc._extract_seniority("Desenvolvedor Júnior Backend") == SeniorityLevel.JUNIOR

    def test_detects_trainee(self, svc):
        assert svc._extract_seniority("Estágio em Desenvolvimento") == SeniorityLevel.JUNIOR

    def test_detects_mid(self, svc):
        assert svc._extract_seniority("Desenvolvedor Pleno Python") == SeniorityLevel.MID

    def test_defaults_to_any_when_ambiguous(self, svc):
        assert svc._extract_seniority("Software Engineer, 5 years experience") == SeniorityLevel.ANY


class TestExtractKeywords:
    def test_returns_at_most_10(self, svc):
        text = " ".join(["word"] * 5 + [f"term{i}" * 2 for i in range(20)])
        result = svc._extract_keywords(text)
        assert len(result) <= 10

    def test_excludes_stopwords(self, svc):
        result = svc._extract_keywords("the and or in for with")
        for sw in ("the", "and", "or", "in", "for", "with"):
            assert sw not in result

    def test_excludes_known_technologies(self, svc):
        result = svc._extract_keywords("python python python backend")
        assert "python" not in result  # python is a known tech, not a free keyword


class TestScoreJob:
    def _job(self, title="", description="", tags=None) -> Job:
        return Job(
            id="x", title=title, company="co",
            location="remote", url="http://x.com",
            description=description, tags=tags or [],
        )

    def test_full_tech_match_gives_70(self, svc):
        resume = ResumeData(path=Path("."), technologies=["python", "fastapi"], keywords=[])
        job = self._job(title="Python FastAPI Developer")
        assert svc.score_job(job, resume) == 70.0

    def test_no_match_gives_zero(self, svc):
        resume = ResumeData(path=Path("."), technologies=["python"], keywords=[])
        job = self._job(title="Java Spring Developer")
        assert svc.score_job(job, resume) == 0.0

    def test_keyword_contributes_30(self, svc):
        resume = ResumeData(path=Path("."), technologies=[], keywords=["microservices"])
        job = self._job(description="We build microservices at scale")
        assert svc.score_job(job, resume) == 30.0

    def test_combined_score(self, svc):
        resume = ResumeData(
            path=Path("."),
            technologies=["python"],    # 1/1 → 70
            keywords=["microservices"],  # 1/1 → 30
        )
        job = self._job(title="Python developer", description="microservices architecture")
        assert svc.score_job(job, resume) == 100.0

    def test_empty_resume_gives_zero(self, svc):
        resume = ResumeData(path=Path("."), technologies=[], keywords=[])
        job = self._job(title="Python Developer")
        assert svc.score_job(job, resume) == 0.0

    def test_score_bounded_at_100(self, svc):
        techs = ["python", "fastapi", "docker"]
        resume = ResumeData(path=Path("."), technologies=techs, keywords=["backend"])
        job = self._job(
            title="Python FastAPI Docker Developer",
            description="backend microservices"
        )
        score = svc.score_job(job, resume)
        assert 0.0 <= score <= 100.0
