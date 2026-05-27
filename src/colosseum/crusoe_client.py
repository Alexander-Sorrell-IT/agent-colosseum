"""Crusoe Cloud Managed Inference client — OpenAI-compatible wrapper."""

from __future__ import annotations
import os
import time
from typing import Optional
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

_DEFAULT_BASE = "https://api.inference.crusoecloud.com/v1"


def _is_transient(e: Exception) -> bool:
    """Detect retryable transport-layer errors from the OpenAI SDK / httpx."""
    name = type(e).__name__
    if name in {"APITimeoutError", "APIConnectionError", "ReadTimeout",
                "ConnectTimeout", "RemoteProtocolError"}:
        return True
    # InternalServerError / 502 / 503 from upstream
    status = getattr(e, "status_code", None)
    return status in {502, 503, 504}


class CrusoeClient:
    """Thin wrapper around OpenAI-compatible Crusoe Managed Inference API."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        self.api_key = api_key or os.environ.get("CRUSOE_API_KEY")
        if not self.api_key:
            raise ValueError(
                "CRUSOE_API_KEY not set. Get one at console.crusoecloud.com/foundry"
            )
        self.base_url = base_url or os.environ.get("CRUSOE_BASE_URL", _DEFAULT_BASE)
        # max_retries=0: per-call timeouts must be honored hard. Default retries
        # turn a 60s timeout into 3+ minutes of silent waiting on slow Nemotron Super calls.
        self._client = OpenAI(api_key=self.api_key, base_url=self.base_url, max_retries=0)
        self._call_count = 0
        self._total_latency = 0.0
        self._errors = 0

    def chat(
        self,
        messages: list[dict],
        model: str = "nvidia/Nemotron-3-Super-120B-A12B-FP8",
        temperature: float = 0.7,
        max_tokens: int = 1024,
        tools: Optional[list[dict]] = None,
        tool_choice: str = "auto",
        timeout: float = 60.0,
    ) -> dict:
        """Send a chat completion request. Returns parsed response dict.

        Retries once on transient transport errors (timeout/connection reset).
        SDK-level retries are disabled (max_retries=0) so the user-visible
        timeout stays bounded; we control retry policy here instead.
        """
        kwargs = dict(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = tool_choice

        last_exc: Optional[Exception] = None
        for attempt in (1, 2):
            start = time.monotonic()
            self._call_count += 1
            try:
                response = self._client.chat.completions.create(**kwargs, timeout=timeout)
                elapsed = time.monotonic() - start
                self._total_latency += elapsed

                choice = response.choices[0]
                msg = choice.message
                result = {
                    "content": msg.content or "",
                    "role": msg.role,
                    "finish_reason": choice.finish_reason,
                    "model": response.model,
                    "latency_ms": round(elapsed * 1000, 1),
                    "attempts": attempt,
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
                # Only retry once, and only for transport-level transients
                if attempt == 1 and _is_transient(e):
                    continue
                break

        raise RuntimeError(
            f"Crusoe API error after {attempt} attempt(s): {last_exc}"
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
        }


# Singleton
_client: Optional[CrusoeClient] = None


def get_client() -> CrusoeClient:
    global _client
    if _client is None:
        _client = CrusoeClient()
    return _client
