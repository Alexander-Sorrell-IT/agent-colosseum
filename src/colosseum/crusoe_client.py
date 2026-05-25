"""Crusoe Cloud Managed Inference client — OpenAI-compatible wrapper."""

from __future__ import annotations
import os
import time
from typing import Optional
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

_DEFAULT_BASE = "https://api.inference.crusoecloud.com/v1"


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
        self._client = OpenAI(api_key=self.api_key, base_url=self.base_url)
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
        """Send a chat completion request. Returns parsed response dict."""
        start = time.monotonic()
        self._call_count += 1
        try:
            kwargs = dict(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            if tools:
                kwargs["tools"] = tools
                kwargs["tool_choice"] = tool_choice

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
            }

            if msg.tool_calls:
                result["tool_calls"] = [
                    {
                        "id": tc.id,
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    }
                    for tc in msg.tool_calls
                ]

            return result

        except Exception as e:
            self._errors += 1
            elapsed = time.monotonic() - start
            self._total_latency += elapsed
            raise RuntimeError(
                f"Crusoe API error (call #{self._call_count}, "
                f"{elapsed:.1f}s): {e}"
            ) from e

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
