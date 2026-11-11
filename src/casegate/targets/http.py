"""A target that POSTs each case to an HTTP service.

It lets a team eval an agent written in any language, or a deployed one. The status code
decides retries: 429 and 5xx are passing faults worth another try, other 4xx are bugs.
The client opens on the first call, so building the target for validation costs nothing.
"""

from __future__ import annotations

from typing import Any

import httpx

from casegate.errors import HttpStatusRetryable
from casegate.models import Output

DEFAULT_TIMEOUT_S = 60.0


class HttpTarget:
    def __init__(self, url: str, headers: dict[str, str], timeout_s: float | None = None) -> None:
        self.url = url
        self.headers = headers
        self.timeout_s = timeout_s if timeout_s is not None else DEFAULT_TIMEOUT_S
        self._client: httpx.AsyncClient | None = None

    async def run(self, case_input: dict[str, Any], *, case_id: str = "") -> Output:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=self.timeout_s)
        response = await self._client.post(
            self.url, json={"case_id": case_id, "input": case_input}, headers=self.headers
        )
        status = response.status_code
        if status == 429 or status >= 500:
            raise HttpStatusRetryable(status, _retry_after_seconds(response))
        if not response.is_success:
            raise RuntimeError(f"HTTP {status}: {response.text[:200]}")
        # A malformed body is a target bug, so pydantic's error is not retried.
        return Output.model_validate_json(response.content)

    async def aclose(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None


def _retry_after_seconds(response: httpx.Response) -> float | None:
    header = response.headers.get("retry-after")
    if header is None:
        return None
    try:
        return float(header)
    except ValueError:  # an HTTP date instead of seconds: fall back to backoff
        return None
