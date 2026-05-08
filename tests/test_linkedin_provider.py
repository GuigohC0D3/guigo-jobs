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
