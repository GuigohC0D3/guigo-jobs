from __future__ import annotations

import time
from typing import Any, Optional

import httpx

from app.core.config import settings
from app.core.logger import logger


class HttpClient:
    def __init__(self) -> None:
        self._client = httpx.Client(
            timeout=settings.request_timeout,
            headers={"User-Agent": settings.user_agent},
            follow_redirects=True,
        )

    def get(
        self,
        url: str,
        params: Optional[dict] = None,
        headers: Optional[dict] = None,
    ) -> Optional[dict | list]:
        for attempt in range(1, settings.max_retries + 1):
            try:
                response = self._client.get(url, params=params, headers=headers)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:
                    wait = settings.retry_delay * attempt * 2
                    logger.warning(f"Rate limited on {url}, waiting {wait}s (attempt {attempt})")
                    time.sleep(wait)
                elif e.response.status_code >= 500:
                    logger.warning(f"Server error {e.response.status_code} on {url} (attempt {attempt})")
                    time.sleep(settings.retry_delay * attempt)
                else:
                    logger.error(f"HTTP {e.response.status_code} on {url}: {e}")
                    return None
            except (httpx.ConnectError, httpx.TimeoutException) as e:
                logger.warning(f"Connection error on {url} (attempt {attempt}): {e}")
                time.sleep(settings.retry_delay * attempt)
            except Exception as e:
                logger.error(f"Unexpected error fetching {url}: {e}")
                return None

        logger.error(f"All {settings.max_retries} attempts failed for {url}")
        return None

    def get_text(self, url: str, params: Optional[dict] = None) -> Optional[str]:
        for attempt in range(1, settings.max_retries + 1):
            try:
                response = self._client.get(url, params=params)
                response.raise_for_status()
                return response.text
            except Exception as e:
                logger.warning(f"Text fetch failed on {url} (attempt {attempt}): {e}")
                time.sleep(settings.retry_delay * attempt)
        return None

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "HttpClient":
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()


http_client = HttpClient()
