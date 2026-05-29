"""THE MIND — one-mind Streamlit chat (WI-5).

You talk to ONE mind (Nemotron). The other Crusoe models are slots inside it; you can see them
think and compose the mind by toggling slots (NOT a model picker — there is no menu of models to
chat with). One photoreal face morphs with the active slots. No tabs, no pickers.

Run:  streamlit run demo/mind_app.py   (after: .venv/bin/python scripts/prewarm_faces.py)
"""

from __future__ import annotations

import base64
import os
import pathlib
import sys

import streamlit as st
from dotenv import load_dotenv

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "src"))
load_dotenv()  # pick up CRUSOE_*/PERFECT_CORP_* from .env, like the CLI does

from colosseum.mind import Mind          # noqa: E402
from colosseum.face import FaceGenerator  # noqa: E402
from colosseum.llm import LLMClient       # noqa: E402

DEGRADED_REPLY = "My thoughts didn't converge into a reply just now — try again."
FACE_CACHE = str(pathlib.Path(__file__).resolve().parent / "face_cache")

st.set_page_config(page_title="The Mind", page_icon="🧠", layout="wide")

st.markdown("""
<style>
  @keyframes breathe { 0%,100% { transform: scale(1); } 50% { transform: scale(1.015); } }
  @keyframes fadein  { from { opacity: 0; } to { opacity: 1; } }
  .face-wrap { display:flex; justify-content:center; }
  .face-img { width:100%; max-width:360px; border-radius:20px;
              box-shadow:0 0 40px rgba(80,120,200,.25);
              animation: breathe 5s ease-in-out infinite; }
  .face-img.morph { animation: fadein .7s ease-in, breathe 5s ease-in-out infinite; }
  .face-ph { width:100%; max-width:360px; aspect-ratio:1; border-radius:20px;
             display:flex; align-items:center; justify-content:center; text-align:center;
             color:#8aa; background:rgba(80,120,200,.08); border:1px dashed rgba(120,150,210,.4);
             animation: breathe 5s ease-in-out infinite; }
  .slot-card { border:1px solid rgba(120,150,210,.25); border-radius:12px; padding:.5rem .75rem;
               margin-bottom:.5rem; }
  .slot-off { opacity:.35; }
</style>
""", unsafe_allow_html=True)


# ── resources (process-global; survive Streamlit reruns) ──
@st.cache_resource
def get_mind() -> Mind | None:
    # The slots are Crusoe models; LLMClient defaults to MIND_*/NVIDIA, so wire Crusoe explicitly.
    try:
        client = LLMClient(api_key=os.environ["CRUSOE_API_KEY"],
                           base_url=os.environ["CRUSOE_BASE_URL"])
    except KeyError:
        return None
    return Mind(client=client)


@st.cache_resource
def get_face_gen() -> FaceGenerator:
    return FaceGenerator(cache_dir=FACE_CACHE)


# ── pure helpers ──
def classify(turn) -> str:
    if turn.blocked and not turn.perspectives:
        return "blocked_in"
    if turn.blocked:
        return "blocked_out"
    if turn.reply == DEGRADED_REPLY:
        return "degraded"
    return "normal"


def history_from_convo(convo: list[dict]) -> list[dict]:
    """Prior turns only (respond() re-adds the current message itself). Bounded to last 8 msgs."""
    msgs: list[dict] = []
    for item in convo:
        msgs.append({"role": "user", "content": item["user"]})
        msgs.append({"role": "assistant", "content": item["turn"].reply})
    return msgs[-8:]


def current_face(gen: FaceGenerator, mind: Mind) -> tuple[str | None, object]:
    key = mind.face_key()
    img = gen.image_for(key, mind.face_prompt())
    return (base64.b64encode(img).decode() if img else None), key


# ── boot ──
mind = get_mind()
if mind is None:
    st.title("🧠 The Mind")
    st.info("Set **CRUSOE_API_KEY** and **CRUSOE_BASE_URL** (see `.env.example`) to wake the mind.")
    st.stop()

gen = get_face_gen()
st.session_state.setdefault("convo", [])          # [{user, turn}]
st.session_state.setdefault("last_face_key", None)

# Sync slot.active from widget state BEFORE rendering the face, so a toggle is reflected this run.
for slot in mind.slots:
    skey = f"slot_{slot.model_id}"
    st.session_state.setdefault(skey, slot.active)
    slot.active = st.session_state[skey]

# ── header ──
left_h, right_h = st.columns([3, 2])
with left_h:
    st.markdown("### 🧠 THE MIND  ·  *Nemotron Super-120B*")
    st.caption("One mind. The other Crusoe models are slots inside it.")
with right_h:
    if st.session_state.convo:
        log = st.session_state.convo[-1]["turn"].gatekeeper_log
        st.caption("boundary  " + "  ".join(f"`{ln}`" for ln in log))

face_col, panel_col = st.columns([1, 1])

# ── the one face ──
with face_col:
    b64, key = current_face(gen, mind)
    changed = key != st.session_state.last_face_key
    st.session_state.last_face_key = key
    if b64:
        cls = "face-img morph" if changed else "face-img"
        st.markdown(f'<div class="face-wrap"><img class="{cls}" '
                    f'src="data:image/jpeg;base64,{b64}"/></div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="face-wrap"><div class="face-ph">…the mind is '
                    'forming a face…</div></div>', unsafe_allow_html=True)
    active = [s.label for s in mind.active_slots]
    st.caption(f"thinking through: {', '.join(active) if active else '— no slots loaded —'}")

# ── minds inside (slot panel + live toggles) ──
with panel_col:
    st.markdown("##### minds inside")
    last_turn = st.session_state.convo[-1]["turn"] if st.session_state.convo else None
    persp_by_id = {p.model_id: p for p in last_turn.perspectives} if last_turn else {}
    for slot in mind.slots:
        skey = f"slot_{slot.model_id}"
        css = "slot-card" if slot.active else "slot-card slot-off"
        st.markdown(f'<div class="{css}">', unsafe_allow_html=True)
        c1, c2 = st.columns([4, 1])
        with c1:
            st.markdown(f"**{slot.label}**  \n<span style='opacity:.7;font-size:.85em'>"
                        f"{slot.lens}</span>", unsafe_allow_html=True)
        with c2:
            st.toggle("on", key=skey, label_visibility="collapsed")
        p = persp_by_id.get(slot.model_id)
        if slot.active and p:
            if p.available:
                st.caption(f"› {p.content}")
            else:
                st.caption("› (slot was unavailable last turn)")
        st.markdown("</div>", unsafe_allow_html=True)


# ── conversation ──
st.divider()
for item in st.session_state.convo:
    with st.chat_message("user"):
        st.markdown(item["user"])
    turn = item["turn"]
    with st.chat_message("assistant"):
        st.markdown(turn.reply)
        kind = classify(turn)
        if kind == "blocked_in":
            st.caption("⛔ stopped at the input boundary")
            with st.expander("minds inside"):
                st.caption("the boundary stopped this before the slots engaged")
        else:
            if kind == "blocked_out":
                st.caption("⛔ reply withheld at the output boundary")
            elif kind == "degraded":
                st.caption("⚠️ the mind didn't converge — try again")
            ps = turn.perspectives
            if ps:
                with st.expander(f"minds inside ({sum(1 for p in ps if p.available)})"):
                    for p in ps:
                        if p.available:
                            st.markdown(f"**{p.label}** — {p.content}")
                        else:
                            st.markdown(f"<span style='opacity:.5'>**{p.label}** — "
                                        f"{p.content}</span>", unsafe_allow_html=True)


# ── input (the ONLY input; respond() runs ONLY here — toggles/reruns cost zero API calls) ──
user_msg = st.chat_input("talk to the mind")
if user_msg:
    history = history_from_convo(st.session_state.convo)
    with st.spinner("the mind is thinking…"):
        turn = mind.respond(user_msg, history)
    st.session_state.convo.append({"user": user_msg, "turn": turn})
    st.rerun()
