"""TrueFoundry AI Gateway client — drop-in alternative to CrusoeClient.

The TF Gateway is OpenAI-compatible: same `chat.completions.create` shape,
different base_url + bearer token. This client routes a chat call through
TF Gateway so we get sponsor-side resilience features (load balancing,
fallback, retry, observability) for free.

Activate by setting:
    TRUEFOUNDRY_API_KEY=...
    TRUEFOUNDRY_BASE_URL=https://gateway.truefoundry.ai
    TRUEFOUNDRY_FALLBACK_MODEL=openai-main/gpt-4o-mini   (or any TF-registered model)

When the env vars are present, callers can construct
`TrueFoundryGatewayClient()` and pass it anywhere `CrusoeClient` is accepted.
It implements the same `.chat(messages, model, ...)` surface.

This is intentionally a *separate* client (not a transparent wrapper around
Crusoe) so the simulation engine can deliberately route specific paths
through TF — e.g. failover when Crusoe browns out, or a TF-backed agent
slot demonstrating cross-provider collaboration.
"""

from __future__ import annotations
import os
import time
from typing import Optional
from openai import OpenAI


_DEFAULT_BASE = "https://gateway.truefoundry.ai"


def _is_transient(e: Exception) -> bool:
    name = type(e).__name__
    if name in {"APITimeoutError", "APIConnectionError", "ReadTimeout",
                "ConnectTimeout", "RemoteProtocolError"}:
        return True
    status = getattr(e, "status_code", None)
    return status in {502, 503, 504}


class TrueFoundryGatewayClient:
    """OpenAI-compatible wrapper around TrueFoundry AI Gateway."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        self.api_key = api_key or os.environ.get("TRUEFOUNDRY_API_KEY")
        if not self.api_key:
            raise ValueError(
                "TRUEFOUNDRY_API_KEY not set. Sign up at https://truefoundry.com, "
                "create a Personal Access Token in Access settings, and export it."
            )
        self.base_url = base_url or os.environ.get("TRUEFOUNDRY_BASE_URL", _DEFAULT_BASE)
        self._client = OpenAI(api_key=self.api_key, base_url=self.base_url, max_retries=0)
        self._call_count = 0
        self._total_latency = 0.0
        self._errors = 0

    def chat(
        self,
        messages: list[dict],
        model: str = "",
        temperature: float = 0.7,
        max_tokens: int = 1024,
        tools: Optional[list[dict]] = None,
        tool_choice: str = "auto",
        timeout: float = 60.0,
    ) -> dict:
        """Send a chat completion through TF Gateway. Same return shape as CrusoeClient."""
        if not model:
            model = os.environ.get("TRUEFOUNDRY_FALLBACK_MODEL", "")
            if not model:
                raise ValueError(
                    "No model specified and TRUEFOUNDRY_FALLBACK_MODEL is unset. "
                    "Pick a model that's been registered in your TF Gateway account."
                )
        kwargs = dict(
            model=model, messages=messages,
            temperature=temperature, max_tokens=max_tokens,
        )
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = tool_choice

        last_exc: Optional[Exception] = None
        for attempt in (1, 2):
            start = time.monotonic()
            self._call_count += 1
            try:
                resp = self._client.chat.completions.create(**kwargs, timeout=timeout)
                elapsed = time.monotonic() - start
                self._total_latency += elapsed
                choice = resp.choices[0]
                msg = choice.message
                result = {
                    "content": msg.content or "",
                    "role": msg.role,
                    "finish_reason": choice.finish_reason,
                    "model": resp.model,
                    "latency_ms": round(elapsed * 1000, 1),
                    "attempts": attempt,
                    "via": "truefoundry-gateway",
                }
                if msg.tool_calls:
                    result["tool_calls"] = [
                        {"id": tc.id, "name": tc.function.name, "arguments": tc.function.arguments}
                        for tc in msg.tool_calls
                    ]
                return result
            except Exception as e:
                self._errors += 1
                self._total_latency += time.monotonic() - start
                last_exc = e
                if attempt == 1 and _is_transient(e):
                    continue
                break

        raise RuntimeError(
            f"TrueFoundry Gateway error after {attempt} attempt(s): {last_exc}"
        ) from last_exc

    @property
    def stats(self) -> dict:
        return {
            "calls": self._call_count,
            "total_latency_ms": round(self._total_latency * 1000, 1),
            "avg_latency_ms": round(
                (self._total_latency / self._call_count * 1000) if self._call_count else 0, 1
            ),
            "errors": self._errors,
            "via": "truefoundry-gateway",
        }


def is_configured() -> bool:
    """Return True if the TF Gateway env vars are present."""
    return bool(os.environ.get("TRUEFOUNDRY_API_KEY"))
