# Resume Import, LinkedIn Provider & TUI Redesign — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add PDF resume import with CV match scoring, LinkedIn job provider, and fix the Textual TUI (replace `Select` with `RadioSet` to unblock keyboard navigation to Gupy region buttons).

**Architecture:** `ResumeService` parses PDF → extracts skills/seniority → pre-fills filters and scores jobs. `LinkedInProvider` fetches from LinkedIn's public guest endpoint with custom User-Agent + stdlib HTML parser. TUI replaces `Select` with `RadioSet` for seniority, adds `ResumeModal`, and enriches job cards with CV badge.

**Tech Stack:** Textual >=0.70, pypdf>=4.0, httpx (already in deps), html.parser (stdlib), tkinter (stdlib, optional for Browse button)

**Spec:** `docs/superpowers/specs/2026-05-08-resume-linkedin-tui-redesign.md`

---

## File Map

| Action | Path | What it does |
|--------|------|-------------|
| Create | `app/services/resume.py` | PDF parse, tech extraction, CV scoring |
| Create | `app/providers/linkedin.py` | LinkedIn guest API provider |
| Create | `tests/test_resume_service.py` | Unit tests for ResumeService |
| Create | `tests/test_linkedin_provider.py` | Unit tests for LinkedInParser |
| Modify | `app/models/job.py` | Add `cv_match_score: float = 0.0` |
| Modify | `app/core/config.py` | Add `enable_linkedin: bool = True` |
| Modify | `app/ui/tui/app.py` | Full TUI redesign |
| Modify | `requirements.txt` | Add `pypdf>=4.0` |

---

## Task 1: Foundation — model, config, requirements

**Files:**
- Modify: `app/models/job.py`
- Modify: `app/core/config.py`
- Modify: `requirements.txt`

- [ ] **Step 1: Add `cv_match_score` to the Job model**

In `app/models/job.py`, add after `relevance_score: float = 0.0` (line 43):

```python
cv_match_score: float = 0.0
```

Final block should look like:
```python
    source: str = ""
    favorited: bool = False
    relevance_score: float = 0.0
    cv_match_score: float = 0.0
```

- [ ] **Step 2: Add LinkedIn toggle to config**

In `app/core/config.py`, add after `enable_greenhouse: bool = False` (line 49):

```python
    enable_linkedin: bool = True
```

- [ ] **Step 3: Add pypdf to requirements**

In `requirements.txt`, add before the `# Dev` comment:

```
pypdf>=4.0
```

- [ ] **Step 4: Install the new dependency**

```bash
pip install pypdf>=4.0
```

Expected: installs pypdf without errors.

- [ ] **Step 5: Run existing tests to confirm nothing broke**

```bash
pytest tests/ -v
```

Expected: all existing tests pass.

- [ ] **Step 6: Commit**

```bash
git add app/models/job.py app/core/config.py requirements.txt
git commit -m "feat: add cv_match_score to Job, enable_linkedin to config, pypdf dep"
```

---

## Task 2: ResumeService — tests first

**Files:**
- Create: `tests/test_resume_service.py`
- Create: `app/services/resume.py` (skeleton only in this task)

- [ ] **Step 1: Create the test file**

Create `tests/test_resume_service.py`:

```python
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
        # All techs + keyword appear in job
        job = self._job(
            title="Python FastAPI Docker Developer",
            description="backend microservices"
        )
        score = svc.score_job(job, resume)
        assert 0.0 <= score <= 100.0
```

- [ ] **Step 2: Run tests — expect ImportError (ResumeService doesn't exist yet)**

```bash
pytest tests/test_resume_service.py -v 2>&1 | head -20
```

Expected: `ImportError: cannot import name 'ResumeData'` or `ModuleNotFoundError`.

- [ ] **Step 3: Create the ResumeService skeleton so tests can be collected**

Create `app/services/resume.py`:

```python
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from app.models.job import Job, SeniorityLevel

_TECHNOLOGIES: frozenset[str] = frozenset({
    # Languages
    "python", "javascript", "typescript", "java", "kotlin", "swift", "go", "golang",
    "rust", "c#", "csharp", "ruby", "php", "scala", "r", "dart", "elixir",
    "haskell", "lua", "perl", "bash", "shell",
    # Frontend
    "react", "vue", "angular", "nextjs", "nuxt", "svelte", "htmx",
    "tailwind", "css", "html", "sass", "webpack", "vite",
    # Backend
    "fastapi", "django", "flask", "express", "nestjs", "spring", "rails",
    "gin", "fiber", "laravel",
    # ML/Data
    "pytorch", "tensorflow", "keras", "scikit-learn", "pandas", "numpy",
    "spark", "hadoop", "airflow", "dbt", "mlflow",
    # Databases
    "postgres", "postgresql", "mysql", "sqlite", "mongodb", "redis",
    "elasticsearch", "cassandra", "dynamodb", "firestore", "supabase",
    # Cloud / Infra
    "aws", "gcp", "azure", "docker", "kubernetes", "k8s", "terraform",
    "ansible", "jenkins", "circleci",
    # Tools
    "git", "linux", "graphql", "rest", "grpc", "kafka", "rabbitmq",
    "nginx", "celery", "figma",
})

_SENIORITY_PATTERNS: dict[SeniorityLevel, re.Pattern] = {
    SeniorityLevel.SENIOR: re.compile(
        r"\b(senior|sr\.?|lead|principal|staff|architect|manager)\b", re.I
    ),
    SeniorityLevel.MID: re.compile(r"\b(mid|pl\.?|pleno|middle)\b", re.I),
    SeniorityLevel.JUNIOR: re.compile(
        r"\b(junior|jr\.?|j[uú]nior|entry.level|trainee|est[aá]gio|intern|graduate)\b", re.I
    ),
}

_STOPWORDS: frozenset[str] = frozenset({
    "the", "and", "or", "in", "on", "at", "to", "for", "of", "with",
    "a", "an", "is", "was", "are", "be", "have", "had", "has", "this",
    "that", "from", "by", "as", "it", "its", "also", "not", "but",
    "de", "da", "do", "em", "no", "na", "ao", "para", "com", "por",
    "e", "ou", "um", "uma", "que", "se", "mais", "como", "seu", "sua",
})


@dataclass
class ResumeData:
    path: Path
    technologies: list[str] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)
    seniority: SeniorityLevel = SeniorityLevel.ANY
    raw_text: str = ""


class ResumeService:
    def parse(self, path: Path) -> ResumeData:
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        text = self._extract_text(path)
        if not text.strip():
            raise ValueError("PDF appears to be image-only or has no extractable text")
        return ResumeData(
            path=path,
            technologies=self._extract_technologies(text),
            keywords=self._extract_keywords(text),
            seniority=self._extract_seniority(text),
            raw_text=text,
        )

    def _extract_text(self, path: Path) -> str:
        from pypdf import PdfReader
        reader = PdfReader(str(path))
        parts = [page.extract_text() or "" for page in reader.pages]
        return "\n".join(parts)

    def _extract_technologies(self, text: str) -> list[str]:
        found = []
        text_lower = text.lower()
        for tech in sorted(_TECHNOLOGIES):
            pattern = re.compile(r"\b" + re.escape(tech) + r"\b", re.I)
            if pattern.search(text_lower):
                found.append(tech)
        return found

    def _extract_keywords(self, text: str) -> list[str]:
        words = re.findall(r"[a-zA-ZÀ-ÿ]{4,}", text.lower())
        freq: dict[str, int] = {}
        for w in words:
            if w not in _STOPWORDS and w not in _TECHNOLOGIES:
                freq[w] = freq.get(w, 0) + 1
        return sorted(freq, key=lambda w: freq[w], reverse=True)[:10]

    def _extract_seniority(self, text: str) -> SeniorityLevel:
        for level in (SeniorityLevel.SENIOR, SeniorityLevel.MID, SeniorityLevel.JUNIOR):
            if _SENIORITY_PATTERNS[level].search(text):
                return level
        return SeniorityLevel.ANY

    def score_job(self, job: Job, resume: ResumeData) -> float:
        if not resume.technologies and not resume.keywords:
            return 0.0

        job_text = f"{job.title} {job.description or ''} {' '.join(job.tags)}".lower()

        tech_total = len(resume.technologies)
        tech_matches = (
            sum(
                1 for t in resume.technologies
                if re.search(r"\b" + re.escape(t) + r"\b", job_text, re.I)
            )
            if tech_total else 0
        )

        kw_total = len(resume.keywords)
        kw_matches = (
            sum(
                1 for k in resume.keywords
                if re.search(r"\b" + re.escape(k) + r"\b", job_text, re.I)
            )
            if kw_total else 0
        )

        tech_score = (tech_matches / tech_total * 70) if tech_total else 0.0
        kw_score = (kw_matches / kw_total * 30) if kw_total else 0.0
        return round(tech_score + kw_score, 1)
```

- [ ] **Step 4: Run the tests — expect all to pass**

```bash
pytest tests/test_resume_service.py -v
```

Expected: all tests PASS. If `test_partial_word_not_matched` fails, check the regex uses `\b` boundaries.

- [ ] **Step 5: Commit**

```bash
git add app/services/resume.py tests/test_resume_service.py
git commit -m "feat: add ResumeService with PDF parsing, skill extraction, and CV scoring"
```

---

## Task 3: LinkedInProvider — tests first

**Files:**
- Create: `tests/test_linkedin_provider.py`
- Create: `app/providers/linkedin.py`

- [ ] **Step 1: Create the test file**

Create `tests/test_linkedin_provider.py`:

```python
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from app.providers.linkedin import LinkedInParser, LinkedInProvider
from app.models.job import SearchFilters, SeniorityLevel


SAMPLE_HTML = """
<ul>
  <li>
    <div class="base-card relative">
      <a class="base-card__full-link absolute" href="https://www.linkedin.com/jobs/view/123?trk=x">Link</a>
      <h3 class="base-search-card__title">Python Developer</h3>
      <h4 class="base-search-card__subtitle"><a>Acme Corp</a></h4>
      <span class="job-search-card__location">Remote</span>
      <time datetime="2024-03-15">1 week ago</time>
    </div>
  </li>
  <li>
    <div class="base-card relative">
      <a class="base-card__full-link absolute" href="https://www.linkedin.com/jobs/view/456">Link</a>
      <h3 class="base-search-card__title">Senior Java Engineer</h3>
      <h4 class="base-search-card__subtitle"><a>Big Corp</a></h4>
      <span class="job-search-card__location">São Paulo, Brazil</span>
      <time datetime="2024-03-10">2 weeks ago</time>
    </div>
  </li>
</ul>
"""

EMPTY_HTML = "<ul></ul>"
MALFORMED_HTML = "<ul><li><div class='base-card'></div></li></ul>"


class TestLinkedInParser:
    def test_parses_two_cards(self):
        cards = LinkedInParser().parse(SAMPLE_HTML)
        assert len(cards) == 2

    def test_extracts_title(self):
        cards = LinkedInParser().parse(SAMPLE_HTML)
        assert cards[0]["title"] == "Python Developer"

    def test_extracts_company(self):
        cards = LinkedInParser().parse(SAMPLE_HTML)
        assert cards[0]["company"] == "Acme Corp"

    def test_extracts_location(self):
        cards = LinkedInParser().parse(SAMPLE_HTML)
        assert cards[0]["location"] == "Remote"

    def test_strips_tracking_params_from_url(self):
        cards = LinkedInParser().parse(SAMPLE_HTML)
        assert cards[0]["url"] == "https://www.linkedin.com/jobs/view/123"
        assert "trk" not in cards[0]["url"]

    def test_extracts_published_at(self):
        cards = LinkedInParser().parse(SAMPLE_HTML)
        assert cards[0]["published_at"] == "2024-03-15"

    def test_empty_html_returns_empty_list(self):
        assert LinkedInParser().parse(EMPTY_HTML) == []

    def test_malformed_card_skipped(self):
        # Card without title should be skipped
        assert LinkedInParser().parse(MALFORMED_HTML) == []

    def test_second_card(self):
        cards = LinkedInParser().parse(SAMPLE_HTML)
        assert cards[1]["title"] == "Senior Java Engineer"
        assert cards[1]["company"] == "Big Corp"


class TestLinkedInProviderFiltering:
    def test_senior_job_filtered_for_junior_search(self):
        from app.providers.linkedin import LinkedInProvider
        provider = LinkedInProvider()
        card = {"title": "Senior Java Engineer", "company": "Co", "url": "http://x.com/1", "location": "Remote"}
        filters = SearchFilters(seniority=SeniorityLevel.JUNIOR)
        job = provider._card_to_job(card, filters)
        assert job is None

    def test_junior_job_passes_for_junior_search(self):
        from app.providers.linkedin import LinkedInProvider
        provider = LinkedInProvider()
        card = {"title": "Junior Python Developer", "company": "Co", "url": "http://x.com/2", "location": "Remote"}
        filters = SearchFilters(seniority=SeniorityLevel.JUNIOR)
        job = provider._card_to_job(card, filters)
        assert job is not None
        assert job.title == "Junior Python Developer"
        assert job.source == "linkedin"

    def test_card_without_url_returns_none(self):
        from app.providers.linkedin import LinkedInProvider
        provider = LinkedInProvider()
        card = {"title": "Python Dev", "company": "Co", "url": "", "location": "Remote"}
        filters = SearchFilters()
        assert provider._card_to_job(card, filters) is None
```

- [ ] **Step 2: Run tests — expect ImportError**

```bash
pytest tests/test_linkedin_provider.py -v 2>&1 | head -10
```

Expected: `ImportError: cannot import name 'LinkedInParser'`.

- [ ] **Step 3: Create the LinkedIn provider**

Create `app/providers/linkedin.py`:

```python
from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from html.parser import HTMLParser
from typing import Any

import httpx

from app.models.job import Job, SearchFilters
from app.providers.base import BaseProvider


_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml",
}

_BASE_URL = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"


class LinkedInParser(HTMLParser):
    """Parses LinkedIn job listing HTML into a list of card dicts."""

    def __init__(self) -> None:
        super().__init__()
        self._cards: list[dict[str, str]] = []
        self._current: dict[str, str] = {}
        self._capture: str | None = None
        self._in_card: bool = False

    def parse(self, html: str) -> list[dict[str, str]]:
        self._cards = []
        self._current = {}
        self._capture = None
        self._in_card = False
        self.feed(html)
        return self._cards

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr = dict(attrs)
        classes = attr.get("class", "") or ""

        if tag == "div" and "base-card" in classes:
            self._current = {}
            self._in_card = True
            return

        if not self._in_card:
            return

        if tag == "a" and "base-card__full-link" in classes:
            href = (attr.get("href") or "").split("?")[0]
            if href:
                self._current["url"] = href
        elif tag == "h3" and "base-search-card__title" in classes:
            self._capture = "title"
        elif tag == "h4" and "base-search-card__subtitle" in classes:
            self._capture = "_company_h4"
        elif tag == "a" and self._capture == "_company_h4":
            self._capture = "company"
        elif tag == "span" and "job-search-card__location" in classes:
            self._capture = "location"
        elif tag == "time":
            self._current["published_at"] = attr.get("datetime", "")

    def handle_endtag(self, tag: str) -> None:
        if self._capture in ("title", "company", "location") and tag in ("h3", "a", "span"):
            self._capture = None
        elif self._capture == "_company_h4" and tag == "h4":
            self._capture = None
        elif tag == "div" and self._in_card and self._current.get("title") and self._current.get("url"):
            self._cards.append(dict(self._current))
            self._in_card = False
            self._current = {}

    def handle_data(self, data: str) -> None:
        if self._capture in ("title", "company", "location"):
            text = data.strip()
            if text:
                existing = self._current.get(self._capture, "")
                self._current[self._capture] = (existing + " " + text).strip()


class LinkedInProvider(BaseProvider):
    name = "linkedin"

    def fetch(self, filters: SearchFilters) -> list[Job]:
        terms = filters.keywords + filters.technologies
        if not terms:
            return []

        parser = LinkedInParser()
        jobs: list[Job] = []

        for start in (0, 25):
            params = {
                "keywords": " ".join(terms[:4]),
                "location": "Remote",
                "f_WT": "2",
                "start": str(start),
            }
            try:
                response = httpx.get(
                    _BASE_URL, params=params, headers=_HEADERS,
                    timeout=15, follow_redirects=True,
                )
                if response.status_code == 429:
                    break
                response.raise_for_status()
            except httpx.HTTPError:
                break

            cards = parser.parse(response.text)
            for card in cards:
                job = self._card_to_job(card, filters)
                if job:
                    jobs.append(job)

            if len(cards) < 25:
                break

        return jobs[: filters.limit]

    def _card_to_job(self, card: dict[str, str], filters: SearchFilters) -> Job | None:
        title = card.get("title", "").strip()
        url = card.get("url", "").strip()

        if not title or not url:
            return None

        if not filters.matches_seniority_keyword(title):
            return None

        job_id = hashlib.md5(url.encode()).hexdigest()[:12]

        pub_date = None
        if dt_str := card.get("published_at"):
            try:
                pub_date = datetime.fromisoformat(dt_str).replace(tzinfo=timezone.utc)
            except ValueError:
                pass

        return Job(
            id=f"linkedin_{job_id}",
            title=title,
            company=card.get("company", "Unknown").strip(),
            location=card.get("location", "Remote").strip(),
            remote=True,
            url=url,
            published_at=pub_date,
            tags=["remote"],
            source=self.name,
        )
```

- [ ] **Step 4: Run tests — expect all to pass**

```bash
pytest tests/test_linkedin_provider.py -v
```

Expected: all tests PASS. If `test_strips_tracking_params_from_url` fails, check `href.split("?")[0]` in `handle_starttag`.

- [ ] **Step 5: Run full test suite**

```bash
pytest tests/ -v
```

Expected: all tests PASS.

- [ ] **Step 6: Commit**

```bash
git add app/providers/linkedin.py tests/test_linkedin_provider.py
git commit -m "feat: add LinkedInProvider with HTML parser for public job listings"
```

---

## Task 4: TUI — Fix RadioSet + LinkedIn integration

**Files:**
- Modify: `app/ui/tui/app.py`

This task fixes the root cause of the Gupy navigation bug (Textual's `Select` dropdown traps keyboard focus). Also wires up LinkedIn to the provider build and sources display.

- [ ] **Step 1: Update imports in `app/ui/tui/app.py`**

Replace the widget imports block (lines 12–27). Remove `Select`, add `RadioButton`, `RadioSet`:

```python
from textual.widgets import (
    Button,
    DataTable,
    Footer,
    Header,
    Input,
    Label,
    ListItem,
    ListView,
    RadioButton,
    RadioSet,
    Rule,
    Static,
    Switch,
    TabbedContent,
    TabPane,
)
```

- [ ] **Step 2: Replace Select CSS with RadioSet CSS**

In the `_CSS` string, find and remove the `Select` and `Select:focus` blocks:
```css
Select {
    background: #161b22;
    border: tall #30363d;
    height: 3;
}

Select:focus {
    border: tall #58a6ff;
}
```

Replace with:
```css
RadioSet {
    border: none;
    background: transparent;
    height: auto;
    padding: 0;
    margin-bottom: 1;
}

RadioSet > RadioButton {
    background: transparent;
    color: #8b949e;
    border: none;
    padding: 0 1 0 0;
}

RadioSet > RadioButton.-on {
    color: #58a6ff;
    text-style: bold;
    background: transparent;
}

RadioSet:focus-within > RadioButton.-on {
    color: #58a6ff;
}
```

- [ ] **Step 3: Replace the `Select` widget with `RadioSet` in `compose()`**

Find this block in `compose()`:
```python
yield Label("Seniority", classes="s-label")
yield Select(
    options=[
        ("Junior", "junior"),
        ("Mid", "mid"),
        ("Senior", "senior"),
        ("Any", "any"),
    ],
    value="junior",
    id="in-sen",
)
```

Replace with:
```python
yield Label("Seniority", classes="s-label")
yield RadioSet(
    RadioButton("Junior", value=True),
    RadioButton("Mid"),
    RadioButton("Senior"),
    RadioButton("Any"),
    id="in-sen",
)
```

- [ ] **Step 4: Update `_get_filters()` to read from RadioSet instead of Select**

Find `_get_filters()` and replace:
```python
sen_val = self.query_one("#in-sen", Select).value
```
and:
```python
seniority=SeniorityLevel(sen_val) if sen_val is not Select.BLANK else SeniorityLevel.JUNIOR,
```

With:
```python
_SEN_OPTIONS = [SeniorityLevel.JUNIOR, SeniorityLevel.MID, SeniorityLevel.SENIOR, SeniorityLevel.ANY]
radio_set = self.query_one("#in-sen", RadioSet)
pressed = radio_set.pressed_index
seniority = _SEN_OPTIONS[pressed] if pressed is not None else SeniorityLevel.JUNIOR
```

The full updated `_get_filters` method:
```python
def _get_filters(self) -> SearchFilters:
    kw_raw = self.query_one("#in-kw", Input).value
    tech_raw = self.query_one("#in-tech", Input).value
    remote = self.query_one("#in-remote", Switch).value
    days_raw = self.query_one("#in-days", Input).value

    _SEN_OPTIONS = [SeniorityLevel.JUNIOR, SeniorityLevel.MID, SeniorityLevel.SENIOR, SeniorityLevel.ANY]
    pressed = self.query_one("#in-sen", RadioSet).pressed_index
    seniority = _SEN_OPTIONS[pressed] if pressed is not None else SeniorityLevel.JUNIOR

    return SearchFilters(
        keywords=[k.strip() for k in kw_raw.split(",") if k.strip()],
        technologies=[t.strip() for t in tech_raw.split(",") if t.strip()],
        seniority=seniority,
        remote_only=remote,
        max_days_old=int(days_raw) if days_raw.strip().isdigit() else None,
    )
```

- [ ] **Step 5: Add LinkedIn to `_sources_text()`**

Find `_sources_text()` and add LinkedIn to the `intl` list after `enable_themuse`:
```python
if settings.enable_themuse:
    intl.append("themuse")
if settings.enable_linkedin:
    intl.append("linkedin")
```

- [ ] **Step 6: Add LinkedIn to `_build_providers()`**

In `_build_providers()`, add the import and provider after `TheMuseProvider`:
```python
from app.providers.linkedin import LinkedInProvider
```
and:
```python
if settings.enable_linkedin:
    intl.append(LinkedInProvider())
```

Full updated `_build_providers`:
```python
def _build_providers(self):
    from app.providers.arbeitnow import ArbeitnowProvider
    from app.providers.gupy import GupyProvider
    from app.providers.linkedin import LinkedInProvider
    from app.providers.remoteok import RemoteOKProvider
    from app.providers.remotive import RemotiveProvider
    from app.providers.themuse import TheMuseProvider

    intl = []
    if settings.enable_remoteok:
        intl.append(RemoteOKProvider())
    if settings.enable_remotive:
        intl.append(RemotiveProvider())
    if settings.enable_arbeitnow:
        intl.append(ArbeitnowProvider())
    if settings.enable_themuse:
        intl.append(TheMuseProvider())
    if settings.enable_linkedin:
        intl.append(LinkedInProvider())

    br = [GupyProvider()] if settings.enable_gupy else []

    if self._region == "brazil":
        return br
    elif self._region == "global":
        return intl
    return intl + br
```

- [ ] **Step 7: Launch TUI and verify the fix**

```bash
python main.py
```

Verify:
1. Seniority shows as `◉ Junior  ○ Mid  ○ Senior  ○ Any` — navigate with `←/→`
2. Press `Tab` after seniority — focus moves to `Remote only` switch, then to `Max days old`, then to region buttons
3. Click `🇧🇷 Brasil` — confirms Gupy navigation bug is fixed
4. Sources bar shows `linkedin` when region is Global or Both

- [ ] **Step 8: Commit**

```bash
git add app/ui/tui/app.py
git commit -m "fix: replace Select with RadioSet for seniority — fixes keyboard nav to Gupy region buttons; add LinkedIn provider to TUI"
```

---

## Task 5: TUI — Resume modal and state management

**Files:**
- Modify: `app/ui/tui/app.py`

- [ ] **Step 1: Add `ResumeData` import and app state**

At the top of `app/ui/tui/app.py`, add to the imports:
```python
from typing import Optional
```
(already there — just confirm it's present)

Also add after existing service imports:
```python
from app.services.resume import ResumeData, ResumeService
```

In `GuigoTUI.__init__`, add after `self._jobs: list[Job] = []`:
```python
self._resume: Optional[ResumeData] = None
```

- [ ] **Step 2: Add the `R` keybinding**

In `BINDINGS`, add:
```python
Binding("r", "do_resume", "Resume"),
```

Full updated `BINDINGS`:
```python
BINDINGS = [
    Binding("ctrl+s", "do_search", "Search"),
    Binding("r", "do_resume", "Resume"),
    Binding("e", "do_export", "Export"),
    Binding("f2", "show_results", "Results"),
    Binding("f3", "show_favs", "Favorites"),
    Binding("f4", "show_hist", "History"),
    Binding("q", "quit", "Quit", priority=True),
]
```

- [ ] **Step 3: Add Resume section to the sidebar in `compose()`**

In the `compose()` method, inside the `with Vertical(id="sidebar"):` block, add this **before** `yield Label("Keywords", ...)`:

```python
yield Label("Resume", classes="s-label")
with Horizontal(id="resume-row"):
    yield Static("[#484f58]✗ No resume[/#484f58]", id="resume-status")
    yield Button("⊕", id="btn-resume", classes="resume-btn")
```

- [ ] **Step 4: Add CSS for the resume section**

In the `_CSS` string, after the `#sources-info` block, add:

```css
/* ── Resume section ──────────────────────────────── */
#resume-row {
    height: auto;
    margin-bottom: 1;
}

#resume-status {
    width: 1fr;
    height: 1;
    content-align: left middle;
}

.resume-btn {
    width: 3;
    height: 1;
    border: none;
    min-width: 3;
    background: #21262d;
    color: #8b949e;
}

.resume-btn:hover {
    background: #30363d;
    color: #e6edf3;
}
```

- [ ] **Step 5: Add the `ResumeModal` class**

Add this class to `app/ui/tui/app.py` **before** the `GuigoTUI` class:

```python
class ResumeModal(ModalScreen["Optional[ResumeData]"]):
    BINDINGS = [("escape", "close_modal", "Close")]

    def __init__(self) -> None:
        super().__init__()
        self._parsed: Optional[ResumeData] = None

    def compose(self) -> ComposeResult:
        with Vertical(id="resume-box"):
            yield Static("Import Resume (PDF)", id="resume-modal-title")
            yield Label("PDF file path", classes="s-label")
            yield Input(placeholder="/path/to/resume.pdf", id="resume-path")
            with Horizontal(id="resume-top-actions"):
                yield Button("Browse", id="btn-rmbrowse", classes="rm-btn")
                yield Button("Parse PDF", id="btn-rmparse", classes="rm-btn")
            yield Static("", id="resume-preview")
            with Horizontal(id="resume-bot-actions"):
                yield Button("✓ Use this resume", id="btn-rmuse", classes="rm-btn", disabled=True)
                yield Button("Cancel", id="btn-rmcancel", classes="rm-btn")

    def action_close_modal(self) -> None:
        self.dismiss(None)

    @on(Button.Pressed, "#btn-rmcancel")
    def on_cancel(self) -> None:
        self.dismiss(None)

    @on(Button.Pressed, "#btn-rmbrowse")
    def on_browse(self) -> None:
        self._browse_worker()

    @work(thread=True)
    def _browse_worker(self) -> None:
        try:
            import tkinter as tk
            from tkinter import filedialog
            root = tk.Tk()
            root.withdraw()
            root.wm_attributes("-topmost", True)
            path = filedialog.askopenfilename(
                title="Select Resume PDF",
                filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
            )
            root.destroy()
            if path:
                self.call_from_thread(self._set_path, path)
        except Exception:
            self.call_from_thread(
                self.app.notify,
                "Browse unavailable — type the path manually",
                severity="warning",
            )

    def _set_path(self, path: str) -> None:
        self.query_one("#resume-path", Input).value = path

    @on(Button.Pressed, "#btn-rmparse")
    def on_parse(self) -> None:
        path_str = self.query_one("#resume-path", Input).value.strip()
        if not path_str:
            self.app.notify("Enter a file path first", severity="warning")
            return
        self._parse_worker(Path(path_str))

    @work(thread=True)
    def _parse_worker(self, path: Path) -> None:
        try:
            data = ResumeService().parse(path)
            self.call_from_thread(self._on_parsed, data)
        except FileNotFoundError:
            self.call_from_thread(
                self.app.notify, "File not found. Check the path.", severity="error"
            )
        except ValueError as e:
            self.call_from_thread(self.app.notify, str(e), severity="warning")
        except Exception as e:
            self.call_from_thread(
                self.app.notify, f"Could not read PDF: {e}", severity="error"
            )

    def _on_parsed(self, data: ResumeData) -> None:
        self._parsed = data
        techs = ", ".join(data.technologies[:8]) or "none detected"
        kws = ", ".join(data.keywords[:5]) or "—"
        preview = (
            f"[#3fb950]✓ Parsed successfully[/#3fb950]\n"
            f"[#8b949e]Tech:[/#8b949e] [#e3b341]{techs}[/#e3b341]\n"
            f"[#8b949e]Keywords:[/#8b949e] [#c9d1d9]{kws}[/#c9d1d9]\n"
            f"[#8b949e]Seniority:[/#8b949e] [#58a6ff]{data.seniority.value}[/#58a6ff]"
        )
        self.query_one("#resume-preview", Static).update(preview)
        self.query_one("#btn-rmuse", Button).disabled = False

    @on(Button.Pressed, "#btn-rmuse")
    def on_use(self) -> None:
        self.dismiss(self._parsed)
```

- [ ] **Step 6: Add CSS for ResumeModal**

In the `_CSS` string, add after the export modal CSS:

```css
/* ── Resume Modal ──────────────────────────────────── */

ResumeModal {
    align: center middle;
}

#resume-box {
    width: 56;
    height: auto;
    background: #161b22;
    border: solid #30363d;
    padding: 2 3;
}

#resume-modal-title {
    text-align: center;
    color: #58a6ff;
    text-style: bold;
    height: 2;
    margin-bottom: 1;
}

#resume-preview {
    height: auto;
    min-height: 4;
    background: #0d1117;
    border: solid #21262d;
    padding: 1;
    margin-top: 1;
    color: #8b949e;
}

#resume-top-actions {
    height: auto;
    margin-top: 1;
}

#resume-bot-actions {
    height: auto;
    margin-top: 1;
}

.rm-btn {
    margin-right: 1;
    border: none;
}

#btn-rmbrowse { background: #21262d; color: #8b949e; }
#btn-rmbrowse:hover { background: #30363d; }

#btn-rmparse { background: #1f6feb; color: #ffffff; }
#btn-rmparse:hover { background: #388bfd; }

#btn-rmuse { background: #238636; color: #ffffff; }
#btn-rmuse:hover { background: #2ea043; }

#btn-rmcancel { background: #21262d; color: #8b949e; }
#btn-rmcancel:hover { background: #30363d; }
```

- [ ] **Step 7: Wire up the resume action in `GuigoTUI`**

Add these methods to `GuigoTUI`:

```python
# ── Resume ─────────────────────────────────────────────────────────────

def action_do_resume(self) -> None:
    self.push_screen(ResumeModal(), callback=self._on_resume_imported)

@on(Button.Pressed, "#btn-resume")
def on_resume_btn(self) -> None:
    self.push_screen(ResumeModal(), callback=self._on_resume_imported)

def _on_resume_imported(self, data: Optional[ResumeData]) -> None:
    if data is None:
        return
    self._resume = data

    if data.technologies:
        self.query_one("#in-tech", Input).value = ", ".join(data.technologies[:6])
    if data.keywords:
        self.query_one("#in-kw", Input).value = ", ".join(data.keywords[:3])

    _SEN_OPTIONS = [SeniorityLevel.JUNIOR, SeniorityLevel.MID, SeniorityLevel.SENIOR, SeniorityLevel.ANY]
    sen_idx = _SEN_OPTIONS.index(data.seniority) if data.seniority in _SEN_OPTIONS else 3
    buttons = list(self.query_one("#in-sen", RadioSet).query(RadioButton))
    if 0 <= sen_idx < len(buttons):
        buttons[sen_idx].value = True

    self.query_one("#resume-status", Static).update(
        f"[#3fb950]✓ {data.path.name}[/#3fb950]"
    )
    self.notify(
        f"Resume loaded — {len(data.technologies)} technologies, seniority: {data.seniority.value}",
        severity="information",
    )
```

- [ ] **Step 8: Also add `Path` import at the top of `app.py` if not present**

Confirm `from pathlib import Path` is in the imports. If missing, add it.

- [ ] **Step 9: Launch TUI and test the flow**

```bash
python main.py
```

Verify:
1. Press `R` — `ResumeModal` opens
2. Enter a PDF path (or click Browse)
3. Click `Parse PDF` — preview shows technologies and seniority
4. Click `✓ Use this resume` — sidebar `Keywords`, `Technologies`, `Seniority` fields pre-filled
5. Resume status in sidebar shows `✓ yourfile.pdf`

- [ ] **Step 10: Commit**

```bash
git add app/ui/tui/app.py
git commit -m "feat: add ResumeModal with PDF import, skill preview, and filter pre-fill"
```

---

## Task 6: TUI — CV match badge + job card polish + CSS cleanup

**Files:**
- Modify: `app/ui/tui/app.py`

- [ ] **Step 1: Update `_search_worker` to apply CV scoring after search**

Find `_search_worker` and add CV scoring after the search:

```python
@work(thread=True, exclusive=True)
def _search_worker(self, filters: SearchFilters, providers: list) -> None:
    from app.services.search import SearchService
    svc = SearchService(providers=providers)
    jobs = svc.search(filters)

    if self._resume:
        resume_svc = ResumeService()
        for job in jobs:
            job.cv_match_score = resume_svc.score_job(job, self._resume)

    self._history.add(filters, len(jobs))
    self.call_from_thread(self._on_search_done, jobs)
```

- [ ] **Step 2: Update `JobItem.__init__` to accept `resume_loaded` flag**

The `JobItem` already has `_is_fav`. We just need to check `job.cv_match_score > 0` at render time — no extra parameter needed since `cv_match_score` is on the `Job` model itself.

- [ ] **Step 3: Update `JobItem.compose()` to render CV badge and source colors**

Replace the entire `JobItem.compose()` method:

```python
def compose(self) -> ComposeResult:
    j = self._job
    fav = "  [bold yellow]★[/bold yellow]" if self._is_fav else ""
    score = j.relevance_score
    sc = "#3fb950" if score >= 5 else "#e3b341" if score >= 2 else "#484f58"

    cv_badge = ""
    if j.cv_match_score > 0:
        pct = int(j.cv_match_score)
        cc = "#3fb950" if pct >= 70 else "#e3b341" if pct >= 40 else "#484f58"
        cv_badge = f"  [{cc}][CV {pct}%][/{cc}]"

    _SRC_COLORS = {"gupy": "#3fb950", "linkedin": "#0a66c2"}
    src_color = _SRC_COLORS.get(j.source, "#79c0ff")

    line1 = (
        f"[bold #8b949e]#{self._index}[/bold #8b949e]  "
        f"[bold #e6edf3]{j.title}[/bold #e6edf3]"
        f"  [{sc}]↑{score:.1f}[/{sc}]{cv_badge}{fav}"
    )

    meta = f"[#d2a8ff]{j.company}[/#d2a8ff]  [#484f58]·[/#484f58]  [#8b949e]{j.location}[/#8b949e]"
    if j.salary:
        meta += f"  [#484f58]·[/#484f58]  [#3fb950]{j.salary}[/#3fb950]"
    if j.published_at:
        from datetime import datetime, timezone
        pub = j.published_at
        if pub.tzinfo is None:
            pub = pub.replace(tzinfo=timezone.utc)
        days = (datetime.now(timezone.utc) - pub).days
        age = f"  [#484f58]· {days}d ago[/#484f58]" if days > 0 else "  [#484f58]· today[/#484f58]"
        meta += age

    tags = "  ".join(f"[#e3b341]{t}[/#e3b341]" for t in j.tags[:5])
    src_badge = f"[{src_color}][{j.source}][/{src_color}]"
    line3 = f"{tags}  {src_badge}" if tags else src_badge

    yield Static(f"{line1}\n{meta}\n{line3}")
```

- [ ] **Step 4: Update status bar to mention CV when active**

In `_on_search_done`, update the success status message to include CV info when loaded:

```python
def _on_search_done(self, jobs: list[Job]) -> None:
    self._jobs = jobs
    self._populate_job_list("#job-list", jobs)
    self._refresh_hist_table()
    self.query_one("#tabs", TabbedContent).active = "tab-results"

    region_label = {"global": "🌐 Global", "brazil": "🇧🇷 Brasil", "both": "⊕ Both"}[self._region]
    cv_hint = "  [#6e40c9]· CV match active[/#6e40c9]" if self._resume else ""

    if jobs:
        self._set_status(
            f"[#3fb950]{len(jobs)} jobs found[/#3fb950]"
            f"  [#484f58]· {region_label} · ranked by relevance[/#484f58]"
            f"{cv_hint}"
        )
        self.notify(f"Found {len(jobs)} jobs", severity="information")
    else:
        self._set_status(
            f"[#f85149]No jobs found[/#f85149]"
            f"  [#484f58]· {region_label} · try broader filters[/#484f58]"
        )
        self.notify("No jobs found", severity="warning")
```

- [ ] **Step 5: Launch TUI and verify CV match flow**

```bash
python main.py
```

Verify:
1. Import a resume with `R`
2. Run a search (`Ctrl+S`)
3. Job cards show `[CV 83%]` badge (or whatever score) in the correct color
4. Status bar shows `· CV match active` when resume is loaded
5. Cards without CV score show no badge

- [ ] **Step 6: Run full test suite one final time**

```bash
pytest tests/ -v
```

Expected: all tests PASS.

- [ ] **Step 7: Commit**

```bash
git add app/ui/tui/app.py
git commit -m "feat: CV match badge on job cards, colored source tags, status bar CV indicator"
```

---

## Self-Review

**Spec coverage check:**
- [x] PDF resume import — Task 2 (ResumeService) + Task 5 (ResumeModal)
- [x] Filters pre-filled from CV — Task 5, `_on_resume_imported`
- [x] CV match score per job — Task 2 (score_job) + Task 6 (badge)
- [x] LinkedIn provider (no auth) — Task 3
- [x] Gupy navigation bug fix (RadioSet) — Task 4
- [x] LinkedIn in sources sidebar — Task 4
- [x] `enable_linkedin` config toggle — Task 1
- [x] `pypdf` dependency — Task 1
- [x] Browse button (tkinter) — Task 5
- [x] Error handling (PDF not found, image-only, 429) — Task 2 + Task 3 + Task 5
- [x] Source badge colors per provider — Task 6
- [x] Published date on cards — Task 6

**Type consistency:**
- `ResumeData` defined in Task 2, used in Task 5 — consistent
- `score_job(job, resume)` signature matches across Task 2 (definition) and Task 6 (call)
- `RadioSet.pressed_index` used in Task 4 (`_get_filters`) and Task 5 (`_on_resume_imported`) — consistent
- `cv_match_score` added in Task 1, scored in Task 6, rendered in Task 6 — consistent

**No placeholders found.**
