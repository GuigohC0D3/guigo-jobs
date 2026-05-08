from __future__ import annotations

import json
import uuid
from datetime import datetime
from pathlib import Path

from app.core.config import settings
from app.models.job import SearchFilters
from app.models.search_history import SearchRecord


class HistoryStorage:
    MAX_RECORDS = 100

    def __init__(self) -> None:
        self._path: Path = settings.storage_dir / "history.json"
        self._records: list[dict] = self._load()

    def _load(self) -> list[dict]:
        if self._path.exists():
            try:
                return json.loads(self._path.read_text(encoding="utf-8"))
            except Exception:
                return []
        return []

    def _save(self) -> None:
        self._path.write_text(
            json.dumps(self._records[-self.MAX_RECORDS :], indent=2, ensure_ascii=False, default=str),
            encoding="utf-8",
        )

    def add(self, filters: SearchFilters, results_count: int) -> SearchRecord:
        record = SearchRecord(
            id=str(uuid.uuid4())[:8],
            filters=filters,
            results_count=results_count,
            timestamp=datetime.now(),
        )
        self._records.append(record.to_dict())
        self._save()
        return record

    def all(self) -> list[SearchRecord]:
        records = []
        for item in reversed(self._records):
            try:
                records.append(SearchRecord(**item))
            except Exception:
                pass
        return records

    def clear(self) -> None:
        self._records = []
        self._save()
