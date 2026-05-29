"""THROWAWAY face spike (WI-0) — not engine code.

Answers the one gating question for the VISION face architecture:
can Perfect Corp give us a PHOTOREAL face whose IDENTITY is stable across calls,
and at what LATENCY? Forks P3 between:
  (a) text_to_image from-scratch  vs.  (b) one base portrait + image-to-image edits.

Run:  .venv/bin/python scripts/face_spike.py
Outputs land in scripts/face_spike_out/ for eyeballing.
"""

from __future__ import annotations

import os
import sys
import time
import pathlib

import requests
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "src"))

from colosseum.perfect_corp_client import get_perfect_client  # noqa: E402

OUT = pathlib.Path(__file__).resolve().parent / "face_spike_out"
OUT.mkdir(exist_ok=True)
SAMPLE_FACE = pathlib.Path(__file__).resolve().parent.parent / "demo" / "sample_faces" / "test_face_tight.jpg"

# Discriminating test (advisor): ONE fixed identity anchor, GENUINELY different moods.
# Same person across all three => from-scratch holds identity through real variation.
# Different people => from-scratch is dead for the morph.
_ANCHOR = ("photorealistic studio portrait of the SAME 32-year-old person: short dark brown "
           "hair, grey-green eyes, light stubble, oval face, straight nose; neutral grey "
           "background, soft frontal studio lighting, 50mm, looking straight at camera, "
           "sharp focus, photo not illustration")
MOOD_PROMPTS = {
    "neutral":    f"{_ANCHOR}; calm neutral resting expression",
    "analytical": f"{_ANCHOR}; intense severe analytical expression, slight frown, focused eyes",
    "playful":    f"{_ANCHOR}; warm open genuine smile, relaxed friendly expression",
}


def _collect_images(obj, urls: list[str], b64s: list[str]) -> None:
    """Recursively walk a result dict; gather http(s) URLs and long base64 blobs."""
    if isinstance(obj, dict):
        for v in obj.values():
            _collect_images(v, urls, b64s)
    elif isinstance(obj, list):
        for v in obj:
            _collect_images(v, urls, b64s)
    elif isinstance(obj, str):
        s = obj.strip()
        if s.startswith("http://") or s.startswith("https://"):
            urls.append(s)
        elif len(s) > 500 and all(c.isalnum() or c in "+/=\n" for c in s[:200]):
            b64s.append(s)


def _save_result(result: dict, tag: str) -> list[str]:
    """Extract images from a poll result and save them. Returns saved paths."""
    import base64
    saved: list[str] = []
    urls: list[str] = []
    b64s: list[str] = []
    _collect_images(result, urls, b64s)
    for i, u in enumerate(urls):
        try:
            r = requests.get(u, timeout=30)
            if r.ok and r.content[:4] not in (b"{\n  ", b'{"st'):  # not JSON
                p = OUT / f"{tag}_url{i}.jpg"
                p.write_bytes(r.content)
                saved.append(str(p))
        except Exception as e:
            print(f"    ! url download failed: {e}")
    for i, b in enumerate(b64s):
        try:
            p = OUT / f"{tag}_b64_{i}.jpg"
            p.write_bytes(base64.b64decode(b.replace("\n", ""), validate=False))
            saved.append(str(p))
        except Exception as e:
            print(f"    ! b64 decode failed: {e}")
    return saved


def _timed(label: str, fn):
    print(f"\n=== {label} ===")
    t0 = time.monotonic()
    try:
        res = fn()
    except Exception as e:
        print(f"  EXCEPTION: {type(e).__name__}: {e}")
        return None, 0.0
    dt = time.monotonic() - t0
    status = res.get("status") if isinstance(res, dict) else "?"
    print(f"  status={status}  latency={dt:.1f}s")
    if isinstance(res, dict) and status not in ("success", None):
        print(f"  message: {res.get('message')}")
    return res, dt


def main() -> None:
    pc = get_perfect_client()
    print(f"configured={pc.is_configured}  base={pc.base_url}")
    if not pc.is_configured:
        print("FATAL: PERFECT_CORP_API_KEY not set"); sys.exit(1)

    # 1) Template discovery — the photoreal question.
    for feature in ("text-to-image", "ai-avatar"):
        tpls = pc.list_templates(feature)
        print(f"\n--- templates for '{feature}': {len(tpls)} ---")
        for t in tpls:
            print(f"  id={t.get('id')!r:32} title={t.get('title')!r} cat={t.get('category_name')!r}")

    # Pick a template id to try for each path (override via env after seeing the list).
    t2i_tpl = os.environ.get("SPIKE_T2I_TEMPLATE", "")
    avatar_tpl = os.environ.get("SPIKE_AVATAR_TEMPLATE", "")
    if not t2i_tpl:
        tpls = pc.list_templates("text-to-image")
        t2i_tpl = tpls[0]["id"] if tpls else ""
    if not avatar_tpl:
        tpls = pc.list_templates("ai-avatar")
        avatar_tpl = tpls[0]["id"] if tpls else ""
    print(f"\nusing  text-to-image template = {t2i_tpl!r}   ai-avatar template = {avatar_tpl!r}")

    # 2) DISCRIMINATING TEST: one identity anchor, genuinely different moods.
    if t2i_tpl:
        for mood, prompt in MOOD_PROMPTS.items():
            r, _ = _timed(f"t2i mood={mood}", lambda p=prompt: pc.text_to_image(p, t2i_tpl))
            if r: print("  saved:", _save_result(r.get("result", r), f"mood_{mood}"))

    # 3) img2img with output_count fix — does ANY template stay PHOTO-like?
    if avatar_tpl and SAMPLE_FACE.exists():
        face = SAMPLE_FACE.read_bytes()
        def _img2img(tpl: str) -> dict:
            up = pc._upload_file("ai-avatar", face)
            if "error" in up:
                return {"status": "error", "message": up["error"]}
            body = {"src_file_id": up["file_id"], "template_id": tpl, "output_count": 1}
            task = pc._execute_task("ai-avatar", body, version="v2.0")
            if "error" in task or not task.get("task_id"):
                return {"status": "error", "message": task.get("error", "no task_id"), "raw": task.get("raw")}
            return pc._poll_result("ai-avatar", task["task_id"], version="v2.0")
        ra, _ = _timed(f"img2img tpl={avatar_tpl}", lambda: _img2img(avatar_tpl))
        if ra: print("  saved:", _save_result(ra.get("result", ra), f"img2img_{avatar_tpl}"))

    print(f"\nDONE. Eyeball images in: {OUT}")
    print("Decide: (a) is anything PHOTOREAL?  (b) do t2i_same1 vs t2i_same2 show the SAME person?")
    print("        (c) latency acceptable for per-turn, or is face_key caching mandatory?")
    print("client stats:", pc.stats)


if __name__ == "__main__":
    main()
