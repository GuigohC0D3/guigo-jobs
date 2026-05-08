from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.models.job import SearchFilters


class SearchRecord(BaseModel):
    id: str
    filters: SearchFilters
    results_count: int
    timestamp: datetime
    label: Optional[str] = None

    def to_dict(self) -> dict:
        data = self.model_dump()
        data["timestamp"] = self.timestamp.isoformat()
        return data
