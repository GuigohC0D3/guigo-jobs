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
