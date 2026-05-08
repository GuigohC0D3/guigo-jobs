from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, HttpUrl, field_validator


class SeniorityLevel(str, Enum):
    JUNIOR = "junior"
    MID = "mid"
    SENIOR = "senior"
    LEAD = "lead"
    ANY = "any"


class ContractType(str, Enum):
    FULL_TIME = "full_time"
    PART_TIME = "part_time"
    CONTRACT = "contract"
    FREELANCE = "freelance"
    INTERNSHIP = "internship"
    ANY = "any"


class Job(BaseModel):
    id: str
    title: str
    company: str
    location: str
    remote: bool = True
    salary: Optional[str] = None
    url: str
    published_at: Optional[datetime] = None
    description: Optional[str] = None
    tags: list[str] = []
    contract_type: ContractType = ContractType.ANY
    seniority: SeniorityLevel = SeniorityLevel.ANY
    source: str = ""
    favorited: bool = False
    relevance_score: float = 0.0
    cv_match_score: float = 0.0

    @field_validator("description", mode="before")
    @classmethod
    def truncate_description(cls, v: Optional[str]) -> Optional[str]:
        if v and len(v) > 500:
            return v[:497] + "..."
        return v

    def to_dict(self) -> dict:
        data = self.model_dump()
        if self.published_at:
            data["published_at"] = self.published_at.isoformat()
        return data


class SearchFilters(BaseModel):
    keywords: list[str] = []
    technologies: list[str] = []
    country: Optional[str] = None
    language: Optional[str] = None
    seniority: SeniorityLevel = SeniorityLevel.JUNIOR
    remote_only: bool = True
    contract_type: ContractType = ContractType.ANY
    max_days_old: Optional[int] = 30
    limit: int = 50

    def matches_seniority_keyword(self, title: str) -> bool:
        title_lower = title.lower()
        if self.seniority == SeniorityLevel.ANY:
            return True
        if self.seniority == SeniorityLevel.JUNIOR:
            junior_terms = {"junior", "jr", "entry", "entry-level", "trainee", "intern", "graduate", "júnior"}
            senior_terms = {"senior", "sr", "lead", "principal", "staff", "architect", "manager"}
            has_senior = any(t in title_lower for t in senior_terms)
            if has_senior:
                return False
            has_junior = any(t in title_lower for t in junior_terms)
            return has_junior or not has_senior
        return True
