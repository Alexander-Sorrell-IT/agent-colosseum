"""OpenAI-compatible LLM client for the Mind.

Backend-agnostic: it talks to whatever OpenAI-compatible endpoint the environment
points it at. Today that's NVIDIA NIM (free); in P4 it swaps to the TrueFoundry
gateway by changing two env vars — no engine changes (the client is injectable).

Captures Nemotron's `reasoning_content` separately so the Mind can show its thinking,
and applies the two safeguards the audit/advisor flagged:
  - retry-on-empty with a LARGER token budget (Nemotron reasoning-token starvation),
  - one retry on transient errors (429/5xx/timeouts) — the resilience TF makes real later.
"""

from __future__ import annotations

import os
import re
import time
from typing import Optional

from openai import OpenAI

_DEFAULT_BASE = "https://integrate.api.nvidia.com/v1"
_THINK_RE = re.compile(r"<think>.*?</think>", re.DOTALL)


def _is_transient(e: Exception) -> bool:
    if type(e).__name__ in {
        "APITimeoutError", "APIConnectionError", "RateLimitError",
        "InternalServerError", "ReadTimeout", "ConnectTimeout",
    }:
        return True
    return getattr(e, "status_code", None) in {429, 500, 502, 503, 504}


class LLMClient:
    """Thin OpenAI-compatible client. `.chat()` returns a dict with content + reasoning."""

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.api_key = (api_key or os.environ.get("MIND_API_KEY")
                        or os.environ.get("NVIDIA_API_KEY"))
        if not self.api_key:
            raise ValueError(
                "No LLM key. Set NVIDIA_API_KEY (free at build.nvidia.com) "
                "or MIND_API_KEY (TrueFoundry gateway)."
            )
        self.base_url = (base_url or os.environ.get("MIND_BASE_URL")
                         or os.environ.get("NVIDIA_BASE_URL") or _DEFAULT_BASE)
        self._client = OpenAI(api_key=self.api_key, base_url=self.base_url, max_retries=0)
        self._calls = 0
        self._errors = 0
        self._latency = 0.0

    def chat(self, messages: list[dict], model: str, temperature: float = 0.6,
             max_tokens: int = 2048, timeout: float = 120.0,
             tools: Optional[list[dict]] = None) -> dict:
        kwargs: dict = {"model": model, "messages": messages, "temperature": temperature}
        if tools:
            kwargs["tools"] = tools

        last_exc: Optional[Exception] = None
        attempt = 0
        for attempt, budget in enumerate((max_tokens, max_tokens * 2), start=1):
            kwargs["max_tokens"] = budget
            start = time.monotonic()
            self._calls += 1
            try:
                resp = self._client.chat.completions.create(**kwargs, timeout=timeout)
                self._latency += time.monotonic() - start
                msg = resp.choices[0].message
                content = (msg.content or "").strip()
                reasoning = (getattr(msg, "reasoning_content", None) or "").strip()

                # Defensive: some models inline <think>…</think> in content.
                if "<think>" in content:
                    if not reasoning:
                        m = _THINK_RE.search(content)
                        reasoning = m.group(0)[7:-8].strip() if m else ""
                    content = _THINK_RE.sub("", content).strip()

                # Starvation safeguard: empty content -> retry once with 2x budget.
                if not content and attempt == 1:
                    last_exc = RuntimeError("empty content (token starvation)")
                    continue

                out = {
                    "content": content,
                    "reasoning": reasoning,
                    "finish_reason": resp.choices[0].finish_reason,
                    "model": resp.model,
                    "latency_ms": round((time.monotonic() - start) * 1000, 1),
                    "attempts": attempt,
                }
                if msg.tool_calls:
                    out["tool_calls"] = [
                        {"id": tc.id, "type": "function",
                         "function": {"name": tc.function.name,
                                      "arguments": tc.function.arguments}}
                        for tc in msg.tool_calls
                    ]
                return out
            except Exception as e:  # noqa: BLE001 — we re-raise after retry policy
                self._errors += 1
                self._latency += time.monotonic() - start
                last_exc = e
                if attempt == 1 and _is_transient(e):
                    continue
                break

        raise RuntimeError(f"LLM error after {attempt} attempt(s): {last_exc}") from last_exc

    @property
    def stats(self) -> dict:
        return {
            "calls": self._calls,
            "errors": self._errors,
            "avg_latency_ms": round(self._latency / self._calls * 1000, 1) if self._calls else 0,
            "endpoint": self.base_url,
        }
