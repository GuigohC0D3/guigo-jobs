from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path

from app.core.config import settings
from app.models.job import Job


class ExportService:
    def __init__(self) -> None:
        self._dir = settings.exports_dir

    def _filename(self, ext: str) -> Path:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        return self._dir / f"guigo_jobs_{ts}.{ext}"

    def to_json(self, jobs: list[Job]) -> Path:
        path = self._filename("json")
        data = [j.to_dict() for j in jobs]
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        return path

    def to_csv(self, jobs: list[Job]) -> Path:
        path = self._filename("csv")
        if not jobs:
            path.write_text("", encoding="utf-8")
            return path

        fields = ["title", "company", "location", "salary", "url", "published_at", "source", "tags"]
        with path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
            writer.writeheader()
            for job in jobs:
                row = job.to_dict()
                row["tags"] = ", ".join(job.tags)
                row["published_at"] = job.published_at.strftime("%Y-%m-%d") if job.published_at else ""
                writer.writerow(row)
        return path

    def to_txt(self, jobs: list[Job]) -> Path:
        path = self._filename("txt")
        lines: list[str] = [f"Guigo Jobs Export — {datetime.now().strftime('%Y-%m-%d %H:%M')}", "=" * 60, ""]
        for i, job in enumerate(jobs, 1):
            lines.append(f"{i}. {job.title}")
            lines.append(f"   Company:  {job.company}")
            lines.append(f"   Location: {job.location}")
            if job.salary:
                lines.append(f"   Salary:   {job.salary}")
            lines.append(f"   URL:      {job.url}")
            if job.published_at:
                lines.append(f"   Posted:   {job.published_at.strftime('%Y-%m-%d')}")
            lines.append(f"   Source:   {job.source}")
            lines.append("")
        path.write_text("\n".join(lines), encoding="utf-8")
        return path
