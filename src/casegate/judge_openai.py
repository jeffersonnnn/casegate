"""The judge adapter for any OpenAI-compatible /chat/completions endpoint.

It covers OpenAI, OpenRouter and local servers with plain httpx and JSON-schema output, so
the anthropic SDK stays an optional extra. It lives apart from judge.py only to keep each
file short enough to read in one sitting (SPEC §1b); build_judge imports it on demand.
"""

from __future__ import annotations

import os
from typing import Any

import httpx
from pydantic import ValidationError

from casegate.errors import HttpStatusRetryable, JudgeError, SuiteError
from casegate.judge import JudgeResult, T
from casegate.models import JudgeConfig
from casegate.prices import cost


class OpenAICompatJudge:
    """Any /chat/completions endpoint with JSON-schema output, over plain httpx."""

    provider = "openai"

    def __init__(self, cfg: JudgeConfig, client: httpx.AsyncClient | None = None) -> None:
        self.cfg = cfg
        name = cfg.api_key_env or "OPENAI_API_KEY"
        key = os.environ.get(name)
        if not key:
            raise SuiteError(f"{name} is not set")
        self._key = key
        base = os.environ.get(cfg.base_url_env) or "https://api.openai.com/v1"
        self.base_url = base.rstrip("/")
        self._owns_client = client is None
        self._client = client if client is not None else httpx.AsyncClient(timeout=120.0)
        # Some models reject temperature; once seen, stop sending it for this client's life.
        self._send_temperature = True

    async def _post(self, system: str, prompt: str, schema: type[T], model: str) -> httpx.Response:
        json_schema = {**schema.model_json_schema(), "additionalProperties": False}
        msgs = [{"role": "system", "content": system}, {"role": "user", "content": prompt}]
        body: dict[str, Any] = {
            "model": model,
            "messages": msgs,
            "max_tokens": self.cfg.max_tokens,
            "response_format": {
                "type": "json_schema",
                "json_schema": {"name": schema.__name__, "strict": True, "schema": json_schema},
            },
        }
        if self._send_temperature:
            body["temperature"] = 0
        headers = {"Authorization": f"Bearer {self._key}"}
        return await self._client.post(
            f"{self.base_url}/chat/completions", json=body, headers=headers
        )

    async def grade(
        self, *, system: str, prompt: str, schema: type[T], model: str
    ) -> JudgeResult[T]:
        resp = await self._post(system, prompt, schema, model)
        rejected = resp.status_code == 400 and "temperature" in resp.text.lower()
        if rejected and self._send_temperature:
            self._send_temperature = False
            resp = await self._post(system, prompt, schema, model)  # same grade, not a retry
        status = resp.status_code
        if status == 429 or status >= 500:
            raise HttpStatusRetryable(status, _retry_after(resp))
        if not 200 <= status < 300:
            raise JudgeError(f"HTTP {status}: {resp.text[:200]}")
        try:
            data = resp.json()
            message = data["choices"][0]["message"]
        except (ValueError, LookupError, TypeError) as exc:
            raise JudgeError(f"unexpected response: {resp.text[:200]}") from exc
        content, refusal = message.get("content"), message.get("refusal")
        if content is None or refusal is not None:
            raise JudgeError(f"judge gave no verdict (refusal {str(refusal)[:200]})")
        try:
            parsed = schema.model_validate_json(content)
        except ValidationError as exc:
            raise JudgeError(f"verdict does not match {schema.__name__}: {exc}") from exc
        usage = data.get("usage") or {}
        n_in, n_out = int(usage.get("prompt_tokens", 0)), int(usage.get("completion_tokens", 0))
        return JudgeResult(parsed, n_in, n_out, cost(model, n_in, n_out))

    async def aclose(self) -> None:
        if self._owns_client:
            await self._client.aclose()


def _retry_after(resp: httpx.Response) -> float | None:
    try:
        return float(resp.headers["retry-after"])
    except (KeyError, ValueError):
        return None
