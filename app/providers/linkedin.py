from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from html.parser import HTMLParser

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
