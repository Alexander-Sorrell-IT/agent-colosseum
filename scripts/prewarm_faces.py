"""One-shot offline pre-render of the demo's face loadouts into demo/face_cache.

Warms ONLY the loadouts the demo can show (full default + drop-DeepSeek) so the live demo is
pure cache hits — no 20–40s Perfect Corp stall on screen. Idempotent (a 2nd run hits disk).
Run once before demoing:  .venv/bin/python scripts/prewarm_faces.py
"""

from __future__ import annotations

import os
import sys
import pathlib

from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "src"))

from colosseum.mind import Mind          # noqa: E402
from colosseum.face import FaceGenerator  # noqa: E402
from colosseum.llm import LLMClient       # noqa: E402

CACHE = pathlib.Path(__file__).resolve().parent.parent / "demo" / "face_cache"


def main() -> None:
    try:
        client = LLMClient(api_key=os.environ["CRUSOE_API_KEY"],
                           base_url=os.environ["CRUSOE_BASE_URL"])
    except KeyError:
        print("Set CRUSOE_API_KEY + CRUSOE_BASE_URL first."); sys.exit(1)

    mind = Mind(client=client)
    gen = FaceGenerator(cache_dir=str(CACHE))

    # exactly the loadouts the demo exposes via slot toggles
    loadouts = {"default (all slots)": None,
                "drop DeepSeek": "deepseek-ai/DeepSeek-V4-Pro"}
    for name, drop in loadouts.items():
        for s in mind.slots:
            s.active = (s.model_id != drop)
        img = gen.image_for(mind.face_key(), mind.face_prompt())
        print(f"  {name:22} -> {('ok, ' + str(len(img)) + ' bytes') if img else 'FAILED (app shows breathing placeholder)'}")

    print(f"cache dir: {CACHE}")


if __name__ == "__main__":
    main()
