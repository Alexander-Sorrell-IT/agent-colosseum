"""Face generation for the Mind — turns face-state into a photoreal portrait.

Resolved by the spike (see VISION.md): from-scratch `text_to_image(style_realistic)` + the
Mind's identity-anchor prompt, **cached per face_key**. Generation is ~20–40s, so the cache is
load-bearing, not an optimization. The Mind exposes face-state (`face_key`/`face_prompt`); this
module realizes it. It never blocks a turn — callers decide when to fetch the image.
"""

from __future__ import annotations

import hashlib
import pathlib
from typing import Optional

import requests

from colosseum.perfect_corp_client import PerfectCorpClient, get_perfect_client

REALISTIC_TEMPLATE = "style_realistic"

FaceKey = tuple[tuple[tuple[str, str], ...], str]


def _is_image(data: bytes) -> bool:
    """True only if bytes start with a known image magic — guards against caching junk."""
    return (data[:3] == b"\xff\xd8\xff"                      # JPEG
            or data[:8] == b"\x89PNG\r\n\x1a\n"              # PNG
            or data[:6] in (b"GIF87a", b"GIF89a")            # GIF
            or (data[:4] == b"RIFF" and data[8:12] == b"WEBP"))  # WEBP


def _extract_image(result: dict) -> Optional[bytes]:
    """Pull the first real image out of a Perfect Corp text-to-image result (URL or base64)."""
    import base64

    urls: list[str] = []
    b64s: list[str] = []

    def walk(o):
        if isinstance(o, dict):
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)
        elif isinstance(o, str):
            s = o.strip()
            if s.startswith("http://") or s.startswith("https://"):
                urls.append(s)
            elif len(s) > 500 and all(c.isalnum() or c in "+/=\n" for c in s[:200]):
                b64s.append(s)

    walk(result)
    for u in urls:
        try:
            r = requests.get(u, timeout=30)
            if r.ok and _is_image(r.content):       # real image bytes only
                return r.content
        except Exception:
            continue
    for b in b64s:
        try:
            data = base64.b64decode(b.replace("\n", ""), validate=False)
            if _is_image(data):                     # don't accept decodable-but-junk strings
                return data
        except Exception:
            continue
    return None


class FaceGenerator:
    """Generates and caches the Mind's photoreal portrait, keyed on face-state."""

    def __init__(self, client: Optional[PerfectCorpClient] = None,
                 template_id: str = REALISTIC_TEMPLATE,
                 cache_dir: Optional[str] = None):
        self.client = client or get_perfect_client()
        self.template_id = template_id
        self.cache_dir = pathlib.Path(cache_dir) if cache_dir else None
        if self.cache_dir:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
        # Keyed on (template_id, face_key): different templates must not collide.
        self._mem: dict[tuple[str, FaceKey], bytes] = {}
        self.generations = 0  # real API generations performed (cache misses)

    def _disk_path(self, key: FaceKey) -> Optional[pathlib.Path]:
        if not self.cache_dir:
            return None
        digest = hashlib.sha256(f"{self.template_id}|{key!r}".encode()).hexdigest()[:16]
        return self.cache_dir / f"face_{digest}.jpg"

    def image_for(self, key: FaceKey, prompt: str) -> Optional[bytes]:
        """Return the portrait bytes for a face-state, generating only on a cache miss."""
        mem_key = (self.template_id, key)
        if mem_key in self._mem:
            return self._mem[mem_key]

        path = self._disk_path(key)
        if path and path.exists():
            data = path.read_bytes()
            self._mem[mem_key] = data
            return data

        data = self._generate(prompt)
        if data:
            self._mem[mem_key] = data
            if path:
                path.write_bytes(data)
        return data

    def _generate(self, prompt: str) -> Optional[bytes]:
        self.generations += 1
        try:
            res = self.client.text_to_image(prompt, self.template_id)
        except Exception:  # noqa: BLE001 — face generation must degrade to None, never raise
            return None
        if not isinstance(res, dict) or res.get("status") != "success":
            return None
        return _extract_image(res.get("result", res))
