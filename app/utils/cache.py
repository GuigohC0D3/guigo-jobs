from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any, Optional

from app.core.config import settings


class FileCache:
    def __init__(self, namespace: str = "default") -> None:
        self._dir = settings.storage_dir / "cache" / namespace
        self._dir.mkdir(parents=True, exist_ok=True)
        self._ttl = settings.cache_ttl_minutes * 60

    def _key_path(self, key: str) -> Path:
        hashed = hashlib.sha256(key.encode()).hexdigest()[:16]
        return self._dir / f"{hashed}.json"

    def get(self, key: str) -> Optional[Any]:
        if not settings.cache_enabled:
            return None
        path = self._key_path(key)
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if time.time() - data["ts"] > self._ttl:
                path.unlink(missing_ok=True)
                return None
            return data["value"]
        except Exception:
            return None

    def set(self, key: str, value: Any) -> None:
        if not settings.cache_enabled:
            return
        path = self._key_path(key)
        try:
            path.write_text(
                json.dumps({"ts": time.time(), "value": value}, default=str),
                encoding="utf-8",
            )
        except Exception:
            pass

    def invalidate(self, key: str) -> None:
        self._key_path(key).unlink(missing_ok=True)

    def clear(self) -> int:
        count = 0
        for f in self._dir.glob("*.json"):
            f.unlink(missing_ok=True)
            count += 1
        return count
