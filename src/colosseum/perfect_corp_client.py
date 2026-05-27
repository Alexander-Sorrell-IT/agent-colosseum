"""Perfect Corp YouCam Enterprise (YCE) API client.

Two-step upload flow (verified live):
  1. POST /s2s/v1.0/file/{feature} -> returns file_id + presigned S3 PUT URL
  2. PUT raw image bytes to the presigned URL with the returned Content-Type
  3. POST /s2s/v1.0/task/{feature} with file_id -> returns task_id
  4. GET /s2s/v1.0/task/{feature}?task_id=... -> poll until status=success

Auth: Bearer <PERFECT_CORP_API_KEY>
"""

from __future__ import annotations

import base64
import os
import time
from typing import Optional


_PERFECT_BASE = os.environ.get(
    "PERFECT_CORP_BASE_URL",
    "https://yce-api-01.perfectcorp.com",
)


class PerfectCorpClient:
    """Wrap Perfect Corp YouCam REST API v2 for agent tool use.

    Each feature follows: POST /s2s/v2.0/file/{feature} -> POST /s2s/v2.0/task/{feature}
    -> GET /s2s/v2.0/task/{feature}?task_id=...

    Response images are base64-encoded in API responses or returned as URLs.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("PERFECT_CORP_API_KEY", "")
        self.base_url = _PERFECT_BASE
        self._call_count = 0
        self._total_latency = 0.0

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key)

    def _auth_header(self) -> dict:
        return {"Authorization": f"Bearer {self.api_key}"}

    # ── Low-level API ─────────────────────────────────────────────

    def _upload_file(self, feature: str, image_bytes: bytes,
                     file_name: str = "image.jpg",
                     content_type: str = "image/jpeg") -> dict:
        """Two-step upload: get presigned URL, then PUT raw bytes.

        Args:
            feature: e.g. 'skin-analysis', 'avatar', 'text-to-image'
            image_bytes: raw image bytes (NOT base64)
            file_name: original filename
            content_type: mime type
        Returns: {"file_id": str, "raw": dict} or {"error": str}
        """
        import requests

        start = time.monotonic()
        self._call_count += 1

        # Step 1: request presigned PUT URL
        resp = requests.post(
            f"{self.base_url}/s2s/v1.0/file/{feature}",
            json={"files": [{
                "content_type": content_type,
                "file_name": file_name,
                "file_size": len(image_bytes),
            }]},
            headers={**self._auth_header(), "Content-Type": "application/json"},
            timeout=30,
        )
        self._total_latency += time.monotonic() - start
        if not resp.ok:
            return {"error": f"presign failed: {resp.status_code} {resp.text[:200]}"}

        data = resp.json()
        files = data.get("result", {}).get("files", [])
        if not files:
            return {"error": f"no file slot returned: {data}"}

        file_slot = files[0]
        file_id = file_slot.get("file_id", "")
        upload_reqs = file_slot.get("requests", [])
        if not file_id or not upload_reqs:
            return {"error": f"missing file_id or upload URL: {file_slot}"}

        # Step 2: PUT raw bytes to presigned S3 URL
        up = upload_reqs[0]
        put_start = time.monotonic()
        self._call_count += 1
        put_resp = requests.put(
            up["url"],
            data=image_bytes,
            headers=up.get("headers", {"Content-Type": content_type}),
            timeout=60,
        )
        self._total_latency += time.monotonic() - put_start
        if not put_resp.ok:
            return {"error": f"S3 upload failed: {put_resp.status_code} {put_resp.text[:200]}"}

        return {"file_id": file_id, "raw": data}

    def _execute_task(self, feature: str, body: dict,
                      version: str = "v2.0") -> dict:
        """POST a fully-formed body to /s2s/{version}/task/{feature}. Returns task_id."""
        import requests

        start = time.monotonic()
        self._call_count += 1

        resp = requests.post(
            f"{self.base_url}/s2s/{version}/task/{feature}",
            json=body,
            headers={**self._auth_header(), "Content-Type": "application/json"},
            timeout=30,
        )
        self._total_latency += time.monotonic() - start

        if not resp.ok:
            return {"error": f"task submit failed: {resp.status_code} {resp.text[:300]}"}

        data = resp.json()
        task_id = (data.get("result", {}).get("task_id")
                   or data.get("data", {}).get("task_id")
                   or data.get("task_id")
                   or "")
        return {"task_id": task_id, "raw": data}

    def _poll_result(self, feature: str, task_id: str,
                     version: str = "v2.0",
                     max_wait: float = 180.0, interval: float = 3.0) -> dict:
        """Poll GET /s2s/{version}/task/{feature}/{task_id} until terminal status.

        Response shape (observed live):
          {"status": 200,
           "data": {"task_status": "running"|"success"|"failed",
                    "results": {...},  # populated on success
                    "error": null|str}}
        """
        import requests

        deadline = time.monotonic() + max_wait

        while time.monotonic() < deadline:
            start = time.monotonic()
            self._call_count += 1
            resp = requests.get(
                f"{self.base_url}/s2s/{version}/task/{feature}/{task_id}",
                headers=self._auth_header(),
                timeout=15,
            )
            self._total_latency += time.monotonic() - start

            if not resp.ok:
                return {"status": "error", "message": f"poll failed: {resp.status_code} {resp.text[:200]}"}

            body = resp.json()
            data = body.get("data") or body.get("result") or body
            # task_status is the actual progress field; some endpoints use status
            ts = (data.get("task_status") or data.get("status") or "").lower()

            if ts in ("success", "completed", "done"):
                return {"status": "success", "result": data.get("results") or data.get("result") or data}
            if ts in ("failed", "error"):
                return {"status": "error", "message": str(data.get("error") or data)}

            time.sleep(interval)

        return {"status": "timeout", "message": f"Task {task_id} timed out after {max_wait}s"}

    # ── Template discovery ────────────────────────────────────────

    def list_templates(self, feature: str, limit: int = 100) -> list[dict]:
        """List style templates for a feature (ai-avatar, text-to-image, etc.).

        Each template has: id, title, thumb, category_name.
        Returns up to `limit` templates (first page only).
        """
        import requests
        if not self.is_configured:
            return []
        try:
            r = requests.get(
                f"{self.base_url}/s2s/v2.0/task/template/{feature}",
                headers=self._auth_header(), timeout=15,
            )
            if not r.ok:
                return []
            templates = r.json().get("data", {}).get("templates", [])
            return templates[:limit]
        except Exception:
            return []

    # ── helpers ────────────────────────────────────────────────────

    @staticmethod
    def _as_bytes(image: bytes | str) -> bytes:
        """Accept raw bytes OR base64 string; return raw bytes."""
        if isinstance(image, bytes):
            return image
        s = image.strip()
        if s.startswith("data:"):
            s = s.split(",", 1)[-1]
        try:
            return base64.b64decode(s, validate=False)
        except Exception:
            return s.encode("utf-8")

    # ── Default skin-analysis actions ──────────────────────────────

    DEFAULT_SKIN_ACTIONS = ["wrinkle", "pore", "texture", "acne", "moisture",
                            "dark_circle_v2", "age_spot", "redness", "oiliness", "radiance"]

    # ── High-level API ─────────────────────────────────────────────

    def analyze_skin(self, image: bytes | str,
                     actions: Optional[list[str]] = None) -> dict:
        """AI Skin Analysis (v2.0). Default returns 10 SD action scores."""
        if not self.is_configured:
            return {"status": "error", "message": "Perfect Corp API key not configured"}

        upload = self._upload_file("skin-analysis", self._as_bytes(image))
        if "error" in upload:
            return {"status": "error", "message": upload["error"]}

        body = {
            "src_file_id": upload["file_id"],
            "dst_actions": actions or self.DEFAULT_SKIN_ACTIONS,
            "miniserver_args": {"enable_mask_overlay": True, "format": "json"},
        }
        task = self._execute_task("skin-analysis", body, version="v2.0")
        if "error" in task or not task.get("task_id"):
            return {"status": "error", "message": task.get("error", "no task_id"), "raw": task.get("raw")}
        return self._poll_result("skin-analysis", task["task_id"], version="v2.0")

    def generate_avatar(self, image: bytes | str, template_id: str) -> dict:
        """AI Avatar — apply a stylized template to a face image.

        Use `list_templates('ai-avatar')` to discover template_ids.
        Examples: 'male_royal', 'male_anime_film', 'male_pop_art', 'male_pencil_artwork'.
        """
        if not self.is_configured:
            return {"status": "error", "message": "Perfect Corp API key not configured"}

        upload = self._upload_file("ai-avatar", self._as_bytes(image))
        if "error" in upload:
            return {"status": "error", "message": upload["error"]}

        body = {"src_file_id": upload["file_id"], "template_id": template_id}
        task = self._execute_task("ai-avatar", body, version="v2.0")
        if "error" in task or not task.get("task_id"):
            return {"status": "error", "message": task.get("error", "no task_id"), "raw": task.get("raw")}
        return self._poll_result("ai-avatar", task["task_id"], version="v2.0")

    def text_to_image(self, prompt: str, template_id: str) -> dict:
        """Gen-AI text-to-image (v2.0). Templates: style_clay, style_ink_painting,
        style_pencil_sketch, style_big_eyed_toon, style_dot_art, etc.

        Use `list_templates('text-to-image')` to discover all template_ids.
        Used for trailer hero shots.
        """
        if not self.is_configured:
            return {"status": "error", "message": "Perfect Corp API key not configured"}

        body = {"template_id": template_id, "prompt": prompt}
        task = self._execute_task("text-to-image", body, version="v2.0")
        if "error" in task or not task.get("task_id"):
            return {"status": "error", "message": task.get("error", "no task_id"), "raw": task.get("raw")}
        return self._poll_result("text-to-image", task["task_id"], version="v2.0", max_wait=180.0)

    def makeup_vto(self, image: bytes | str, look_id: str = "natural_glow") -> dict:
        """AI Makeup Virtual Try-On (v2.0). Stub — real makeup VTO requires
        SKU-level color/opacity configuration. Best for beauty consultation demo."""
        if not self.is_configured:
            return {"status": "error", "message": "Perfect Corp API key not configured"}
        upload = self._upload_file("makeup-vto", self._as_bytes(image))
        if "error" in upload:
            return {"status": "error", "message": upload["error"]}
        body = {"src_file_id": upload["file_id"], "look_id": look_id}
        task = self._execute_task("makeup-vto", body, version="v2.0")
        if "error" in task or not task.get("task_id"):
            return {"status": "error", "message": task.get("error", "no task_id")}
        return self._poll_result("makeup-vto", task["task_id"], version="v2.0")

    def analyze_skin_tone(self, image: bytes | str) -> dict:
        """AI Skin Tone Analysis (v2.0). Returns undertone, foundation match."""
        if not self.is_configured:
            return {"status": "error", "message": "Perfect Corp API key not configured"}
        upload = self._upload_file("skin-tone-analysis", self._as_bytes(image))
        if "error" in upload:
            return {"status": "error", "message": upload["error"]}
        body = {"src_file_id": upload["file_id"]}
        task = self._execute_task("skin-tone-analysis", body, version="v2.0")
        if "error" in task or not task.get("task_id"):
            return {"status": "error", "message": task.get("error", "no task_id")}
        return self._poll_result("skin-tone-analysis", task["task_id"], version="v2.0")

    def hair_style_vto(self, image: bytes | str, style_id: str = "") -> dict:
        """AI Hair Style Virtual Try-On (v2.0). Needs template_id from Perfect Corp catalog."""
        if not self.is_configured:
            return {"status": "error", "message": "Perfect Corp API key not configured"}
        upload = self._upload_file("hair-style", self._as_bytes(image))
        if "error" in upload:
            return {"status": "error", "message": upload["error"]}
        body = {"src_file_id": upload["file_id"]}
        if style_id:
            body["template_id"] = style_id
        task = self._execute_task("hair-style", body, version="v2.0")
        if "error" in task or not task.get("task_id"):
            return {"status": "error", "message": task.get("error", "no task_id")}
        return self._poll_result("hair-style", task["task_id"], version="v2.0")

    def fashion_vto(self, image: bytes | str, item_type: str = "cloth",
                    item_id: str = "") -> dict:
        """AI Fashion Virtual Try-On (v2.0). item_type: cloth/bag/shoes/watch/etc."""
        if not self.is_configured:
            return {"status": "error", "message": "Perfect Corp API key not configured"}
        upload = self._upload_file(item_type, self._as_bytes(image))
        if "error" in upload:
            return {"status": "error", "message": upload["error"]}
        body = {"src_file_id": upload["file_id"]}
        if item_id:
            body["template_id"] = item_id
        task = self._execute_task(item_type, body, version="v2.0")
        if "error" in task or not task.get("task_id"):
            return {"status": "error", "message": task.get("error", "no task_id")}
        return self._poll_result(item_type, task["task_id"], version="v2.0")

    @property
    def stats(self) -> dict:
        return {
            "calls": self._call_count,
            "total_latency_ms": round(self._total_latency * 1000, 1),
        }


# Singleton
_perfect_client: Optional[PerfectCorpClient] = None


def get_perfect_client() -> PerfectCorpClient:
    global _perfect_client
    if _perfect_client is None:
        _perfect_client = PerfectCorpClient()
    return _perfect_client
