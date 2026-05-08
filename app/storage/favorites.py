from __future__ import annotations

import json
from pathlib import Path

from app.core.config import settings
from app.models.job import Job


class FavoritesStorage:
    def __init__(self) -> None:
        self._path: Path = settings.storage_dir / "favorites.json"
        self._data: dict[str, dict] = self._load()

    def _load(self) -> dict[str, dict]:
        if self._path.exists():
            try:
                return json.loads(self._path.read_text(encoding="utf-8"))
            except Exception:
                return {}
        return {}

    def _save(self) -> None:
        self._path.write_text(
            json.dumps(self._data, indent=2, ensure_ascii=False, default=str),
            encoding="utf-8",
        )

    def add(self, job: Job) -> None:
        job.favorited = True
        self._data[job.id] = job.to_dict()
        self._save()

    def remove(self, job_id: str) -> bool:
        if job_id in self._data:
            del self._data[job_id]
            self._save()
            return True
        return False

    def toggle(self, job: Job) -> bool:
        if job.id in self._data:
            self.remove(job.id)
            job.favorited = False
            return False
        else:
            self.add(job)
            return True

    def all(self) -> list[Job]:
        jobs = []
        for item in self._data.values():
            try:
                jobs.append(Job(**item))
            except Exception:
                pass
        return jobs

    def is_favorite(self, job_id: str) -> bool:
        return job_id in self._data

    def count(self) -> int:
        return len(self._data)
