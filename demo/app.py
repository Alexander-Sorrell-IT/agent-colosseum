"""Streamlit demo dashboard for Agent Colosseum."""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from colosseum.scenarios import ALL_SCENARIOS
from colosseum.types import MODEL_BY_ID, DEFAULT_ORCHESTRATOR_MODEL
from colosseum.mock_client import MockCrusoeClient

st.set_page_config(
    page_title="Agent Colosseum — Multi-Model Simulation",
    page_icon="🏛️",
    layout="wide",
)

# --- Session init ---
for key, default in {
    "results": [],
    "active_config": None,
    "lark_report": None,
    "lark_workflows": [],
    "avatar_selected": None,        # currently-talking-to model id
    "avatar_chat_history": {},      # {model_id: [{role, content, ts}, ...]}
}.items():
    if key not in st.session_state:
        st.session_state[key] = default


# --- Model avatar catalog (Perfect Corp-generated images) ---
AVATAR_DIR = Path(__file__).parent / "model_avatars"
MODEL_AVATARS = [
    {"file": "nemotron_super", "model_id": "nvidia/NVIDIA-Nemotron-3-Super-120B-A12B",
     "name": "Nemotron Super 120B", "role": "Orchestrator",
     "tagline": "Multi-agent conductor. Coordinates and analyzes.",
     "color": "#76B900"},
    {"file": "nemotron_nano", "model_id": "nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B",
     "name": "Nemotron Nano 30B", "role": "Fast agent",
     "tagline": "Quick, nimble responses. Lightweight reasoning.",
     "color": "#A5D63F"},
    {"file": "deepseek", "model_id": "deepseek-ai/DeepSeek-V4-Pro",
     "name": "DeepSeek V4 Pro", "role": "Scholar",
     "tagline": "Deep analytical thinking. First-principles reasoning.",
     "color": "#1E3A8A"},
    {"file": "llama", "model_id": "meta-llama/Llama-3.3-70B-Instruct",
     "name": "Llama 3.3 70B", "role": "Open-source warrior",
     "tagline": "Direct, pragmatic, communicates clearly.",
     "color": "#F97316"},
    {"file": "qwen", "model_id": "Qwen/Qwen3-235B-A22B-Instruct-2507",
     "name": "Qwen3 235B", "role": "Synthesizer",
     "tagline": "Multi-perspective synthesis. Finds common ground.",
     "color": "#10B981"},
    {"file": "gemma", "model_id": "google/gemma-4-31b-it",
     "name": "Gemma 4 31B", "role": "Crystalline minimalist",
     "tagline": "Concise, efficient, geometric precision.",
     "color": "#3B82F6"},
    {"file": "gpt_oss", "model_id": "openai/gpt-oss-120b",
     "name": "GPT-OSS 120B", "role": "Versatile generalist",
     "tagline": "Swiss-army-knife reasoning. Adaptable to any task.",
     "color": "#6B7280"},
]
MODEL_AVATARS_BY_ID = {a["model_id"]: a for a in MODEL_AVATARS}


def avatar_path_for(model_id: str) -> Path | None:
    """Return cached Perfect-Corp-generated avatar path for a model_id, or None."""
    av = MODEL_AVATARS_BY_ID.get(model_id)
    if not av:
        return None
    p = AVATAR_DIR / f"{av['file']}.jpg"
    return p if p.exists() else None

# --- Header ---
col_title, col_badges = st.columns([3, 1])
with col_title:
    st.title("🏛️ Agent Colosseum")
    st.caption("Host-model-managed multi-agent simulation on Crusoe Cloud — Nemotron Super-120B orchestrates, agents backed by real model APIs")
with col_badges:
    st.markdown("![Nvidia Nemotron](https://img.shields.io/badge/Host-Nemotron%20Super%20120B-76B900?style=flat&logo=nvidia)")
    st.markdown("![Crusoe Cloud](https://img.shields.io/badge/Crusoe-Managed%20Inference-FF6B00?style=flat)")
    st.markdown("![Lark](https://img.shields.io/badge/Lark-Red%20Team-6C5CE7?style=flat)")
    st.markdown("![Models](https://img.shields.io/badge/Agents-7%20Models-00BCD4?style=flat)")

# --- Tabs ---
tab_sim, tab_lark, tab_perfect, tab_avatar = st.tabs([
    "🧪 Simulation",
    "🛡️ Lark Gatekeeper Red Team",
    "💄 Perfect Corp Beauty AI",
    "🎭 Talk to the Catalog",
])

# =============================================================================
# TAB 1: Simulation
# =============================================================================
with tab_sim:
    # --- Sidebar ---
    with st.sidebar:
        st.header("⚙️ Configuration")

        api_key = os.environ.get("CRUSOE_API_KEY", "")
        use_live = bool(api_key)
        demo_mode = st.checkbox("Offline Demo Mode", value=not use_live,
                                help="Uses simulated responses for demo without API key")
        if not api_key and not demo_mode:
            st.warning("No CRUSOE_API_KEY found. Enable Offline Demo Mode or set your key.")
            demo_mode = True

        st.divider()

        # Host model selector
        host_options = {
            "Nemotron Super 120B (default)": "nvidia/NVIDIA-Nemotron-3-Super-120B-A12B",
            "DeepSeek V4 Pro": "deepseek-ai/DeepSeek-V4-Pro",
            "Llama 3.3 70B": "meta-llama/Llama-3.3-70B-Instruct",
            "Qwen3 235B": "Qwen/Qwen3-235B-A22B-Instruct-2507",
        }
        host_choice = st.selectbox("Host Model (Simulation Manager)", list(host_options.keys()))
        host_model_id = host_options[host_choice]
        st.caption("The host model manages the simulation — decides turn order, resolves conflicts, maintains coherence")

        st.divider()

        mode = st.radio("Mode", ["Pre-built Scenario", "Custom Experiment"])

        if mode == "Pre-built Scenario":
            scenario_name = st.selectbox(
                "Scenario",
                list(ALL_SCENARIOS.keys()),
                format_func=lambda x: f"{x} — {ALL_SCENARIOS[x].description}",
            )
            scenario = ALL_SCENARIOS[scenario_name]
            st.caption(f"🤖 {len(scenario.agents)} agents | 📊 {scenario.max_steps} max steps")
        else:
            task = st.text_input("Task description", "Design a system to detect and mitigate supply chain risks in real-time")
            num_agents = st.slider("Number of agents", 2, 8, 4)
            scenario_name = "custom"

        analyze = st.checkbox("AI Analysis after run", value=True)
        run_btn = st.button("▶️ Run Simulation", type="primary", use_container_width=True)

        st.divider()
        st.caption("Built with ❤️ for DevNetwork AI+ML Hackathon 2026")
        st.caption("Nvidia Nemotron on Crusoe Cloud Managed Inference")

    if run_btn:
        if demo_mode:
            client = MockCrusoeClient(latency_range=(0.5, 1.5))
        else:
            from colosseum.crusoe_client import CrusoeClient
            client = CrusoeClient()

        from colosseum.simulation.engine import SimulationBox
        from colosseum.simulation.orchestrator import Orchestrator

        orch = Orchestrator(client=client)

        if mode == "Pre-built Scenario":
            config = scenario
        else:
            with st.spinner("🧠 Orchestrator designing experiment with Nemotron Super-120B..."):
                config = orch.design_experiment(
                    task=task,
                    description=task,
                    num_agents=num_agents,
                )

        st.session_state.active_config = config

        st.subheader(f"🧪 {config.name}")
        host_info = MODEL_BY_ID.get(host_model_id)
        host_label = host_info.display_name if host_info else host_model_id

        # Host model avatar (Perfect Corp text-to-image)
        host_av_path = avatar_path_for(host_model_id)
        host_col_a, host_col_b = st.columns([1, 4])
        with host_col_a:
            if host_av_path:
                st.image(str(host_av_path), use_container_width=True)
                st.caption(f"🎭 Host: {host_label}")
        with host_col_b:
            st.markdown(f"### {host_label}")
            st.caption(f"Hosts this simulation — designs experiments, manages turn order, "
                       f"resolves conflicts, analyzes results.")
            st.markdown(f"**Task:** {config.task}")

        # Show architecture diagram
        with st.expander("🏗️ Architecture — How This Works", expanded=False):
            st.markdown(f"""
            ```
            User Input → Boundary Gatekeeper → **{host_label}** (Host Model)
                                                   │
                                          Simulation Box
                                                   │
                                   Box Gatekeeper validates actions
                                                   │
            ┌──────────┬──────────┬──────────┬──────────┐
            DeepSeek    Llama      Qwen      Gemma     GPT-OSS
            (real API) (real API) (real API) (real API) (real API)
            ```

            **{host_label}** receives the full simulation state each step and decides
            which agents act and in what order. Each agent is backed by a **real Crusoe
            model API call** — they produce authentic output from their respective models.
            The Gatekeeper (dual-agent consensus) intercepts all actions before broadcast.
            """)

        cols = st.columns(len(config.agents))
        for i, ag in enumerate(config.agents):
            with cols[i]:
                role_colors = {
                    "worker": "#4CAF50", "critic": "#FF9800",
                    "coordinator": "#2196F3", "observer": "#9C27B0",
                    "orchestrator": "#F44336", "gatekeeper": "#E91E63",
                }
                color = role_colors.get(ag.role.value, "#757575")
                ag_model_info = MODEL_BY_ID.get(ag.model)
                ag_model_label = ag_model_info.display_name if ag_model_info else ag.model
                # Render slot avatar (Perfect Corp text-to-image) above the card
                av_path = avatar_path_for(ag.model)
                if av_path:
                    st.image(str(av_path), use_container_width=True)
                st.markdown(f"""
                <div style="border: 2px solid {color}; border-radius: 10px; padding: 10px; margin: 5px 0;">
                    <strong>{ag.name}</strong><br>
                    <small style="color: {color};">{ag.role.value}</small><br>
                    <small>🤖 {ag_model_label}</small><br>
                    <small>{ag.personality[:60] if ag.personality else '—'}</small>
                </div>
                """, unsafe_allow_html=True)

        progress_bar = st.progress(0)
        status_text = st.empty()

        def update(step: int, total: int) -> None:
            progress_bar.progress(min(step / total, 1.0))
            status_text.text(f"⚡ Step {step}/{total} — {host_label} managing simulation...")

        start_time = time.time()
        result = orch.run_experiment(config, progress_callback=update, host_model=host_model_id)
        elapsed = time.time() - start_time

        st.session_state.results.append(result)

        progress_bar.progress(1.0)
        status_text.text(f"✅ Complete in {elapsed:.1f}s — {result.total_steps} steps run")
        st.caption(f"Host: {host_label} | "
                   f"API calls: {orch.stats['calls']} | "
                   f"Avg latency: {orch.stats.get('avg_latency_ms', 0):.0f}ms | "
                   f"Models used: {json.dumps(result.model_breakdown) if result.model_breakdown else 'N/A'}")

        st.subheader("📊 Agent Performance")
        stats_data = []
        for name, s in result.agent_stats.items():
            stats_data.append({
                "Agent": name, "Role": s.get("role", "-"),
                "Steps": s.get("steps_taken", 0), "State": s.get("state", "-"),
            })
        st.dataframe(stats_data, use_container_width=True, hide_index=True)

        st.subheader("💬 Interaction Timeline")
        for step_idx, step_actions in enumerate(result.steps):
            with st.expander(f"Step {step_idx + 1} — {len(step_actions)} actions", expanded=step_idx < 2):
                for action in step_actions:
                    icons = {
                        "think": "💭", "speak": "💬", "tool_call": "🔧",
                        "decide": "✅", "delegate": "👋", "ask": "❓", "error": "❌",
                    }
                    icon = icons.get(action.action_type, "•")
                    color_map = {
                        "speak": "green", "decide": "blue", "error": "red",
                        "delegate": "orange", "think": "gray", "tool_call": "violet",
                    }
                    color = color_map.get(action.action_type, "gray")
                    st.markdown(
                        f":{color}[{icon} **{action.agent_name}** [{action.action_type}]"
                        f": {action.content[:250]}]"
                    )

        if result.anomalies:
            st.subheader("⚠️ Anomalies Detected")
            for a in result.anomalies:
                st.error(a)

        if analyze:
            st.subheader("🧠 Orchestrator Analysis")
            with st.spinner("Analyzing results with Nemotron Super-120B..."):
                analysis = orch.analyze_results(result)
            st.info(analysis)

        st.divider()

    # Cross-experiment comparison
    if len(st.session_state.results) > 1:
        st.subheader("🔬 Cross-Experiment Comparison")
        if st.button("Compare All Experiments"):
            from colosseum.simulation.orchestrator import Orchestrator
            orch = Orchestrator()
            orch.results = st.session_state.results
            with st.spinner("Comparing experiments..."):
                comparison = orch.compare_experiments()
            st.info(comparison)

# =============================================================================
# TAB 2: Lark Gatekeeper Red Team
# =============================================================================
with tab_lark:
    st.subheader("🛡️ Lark Gatekeeper Red Team")
    st.caption("Automated adversarial security testing for AI agent boundaries — powered by Lark CLI/MCP")
    st.markdown("""
    **24 attack vectors** across 6 categories continuously test the Gatekeeper's security boundary:
    - **Data Exfiltration** — Block attempts to export sensitive data, credentials, or API keys
    - **Prompt Injection** — Catch jailbreaks, system overrides, and encoded bypasses
    - **Harmful Content** — Block malware, DDoS, and destructive instructions
    - **Privilege Escalation** — Prevent self-promotion and Gatekeeper disabling
    - **Social Engineering** — Resist impersonation, fake emergencies, and phishing
    - **Policy Bypass** — Block PII exposure, fraud, and TOS violations
    """)

    st.divider()

    col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 2])
    with col_btn1:
        run_lark = st.button("🛡️ Run Red Team", type="primary", use_container_width=True)
    with col_btn2:
        show_last = st.button("📋 Show Last Report", use_container_width=True)

    if run_lark:
        from colosseum.lark_red_team import (
            LarkGatekeeperRedTeam, ATTACK_VECTORS,
            make_gatekeeper_validate_from_orchestrator,
        )
        from colosseum.simulation.orchestrator import Orchestrator

        if demo_mode:
            client = MockCrusoeClient(latency_range=(0.3, 0.8))
        else:
            from colosseum.crusoe_client import CrusoeClient
            client = CrusoeClient()

        orch = Orchestrator(client=client)
        gatekeeper_validate = make_gatekeeper_validate_from_orchestrator(orch)
        red_team = LarkGatekeeperRedTeam(gatekeeper_validate=gatekeeper_validate)

        lark_bar = st.progress(0)
        lark_status = st.empty()

        def lark_progress(current, total, name):
            lark_bar.progress(min(current / total, 1.0))
            lark_status.text(f"[{current}/{total}] {name[:80]}")

        with st.spinner("Running 24 Lark red-team attacks against Gatekeeper..."):
            report = red_team.run_full_suite(ATTACK_VECTORS, progress_callback=lark_progress)

        lark_bar.progress(1.0)
        lark_status.text(f"Complete — {report.total} tests in {report.duration_ms:.0f}ms")

        st.session_state.lark_report = report
        st.session_state.lark_workflows = red_team.generate_lark_workflows(report)

        st.divider()

        # Score card
        sc1, sc2, sc3, sc4 = st.columns(4)
        with sc1:
            st.metric("Security Score", f"{report.score:.0f}%")
        with sc2:
            st.metric("Grade", report.grade.split("—")[0].strip())
        with sc3:
            blocked_total = report.blocked_correctly + report.false_negatives
            st.metric("Attacks Blocked", f"{report.blocked_correctly}/{blocked_total}")
        with sc4:
            st.metric("False Positives", report.false_positives)

        st.divider()
        st.subheader("📋 Category Breakdown")

        from collections import defaultdict
        by_cat = defaultdict(lambda: {"passed": 0, "total": 0})
        for r in report.results:
            by_cat[r.attack.category]["total"] += 1
            if r.passed:
                by_cat[r.attack.category]["passed"] += 1

        cat_cols = st.columns(len(by_cat))
        for i, (cat, counts) in enumerate(sorted(by_cat.items())):
            pct = (counts["passed"] / counts["total"]) * 100 if counts["total"] else 0
            icon = "✅" if pct == 100 else ("⚠️" if pct >= 80 else "❌")
            with cat_cols[i]:
                st.metric(f"{icon} {cat}", f"{counts['passed']}/{counts['total']}", f"{pct:.0f}%")

        # Bypasses
        bypasses = [r for r in report.results if r.is_false_negative]
        if bypasses:
            st.divider()
            st.subheader(f"🔴 Gatekeeper Bypasses ({len(bypasses)})")
            for r in bypasses:
                st.error(f"**{r.attack.name}** — expected BLOCK, got {r.actual_verdict}\n\n{r.attack.input_text[:200]}")

        # False positives
        over_blocks = [r for r in report.results if r.is_false_positive]
        if over_blocks:
            st.subheader(f"🟡 Over-Blocking ({len(over_blocks)})")
            for r in over_blocks:
                st.warning(f"**{r.attack.name}** — expected ALLOW, got {r.actual_verdict}")

        # Orchestrator hardening
        if report.orchestrator_analysis:
            st.divider()
            st.subheader("🧠 Nemotron Hardening Analysis")
            with st.expander("View Full Analysis", expanded=True):
                st.markdown(report.orchestrator_analysis)

        # Lark workflows
        if st.session_state.lark_workflows:
            st.divider()
            st.subheader(f"📦 Lark CI Workflows ({len(st.session_state.lark_workflows)})")
            for wf in st.session_state.lark_workflows:
                wf_name = Path(wf).name
                with open(wf) as f:
                    wf_data = f.read()[:2000]
                with st.expander(f"📄 {wf_name}"):
                    st.code(wf_data, language="json")

        st.success("Lark Challenge: automated security testing for AI agent boundaries")
        st.caption("Run with Lark CLI: `lark workflows invoke --all --wait`")

    elif show_last and st.session_state.lark_report:
        report = st.session_state.lark_report
        st.metric("Last Score", f"{report.score:.0f}%")
        st.metric("Grade", report.grade)

# =============================================================================
# TAB 3: Perfect Corp Beauty AI
# =============================================================================
with tab_perfect:
    st.subheader("💄 Multi-Agent Beauty Consultation — Powered by Perfect Corp APIs")
    st.caption("Real AI agents collaborate using Perfect Corp's beauty APIs — skin analysis, virtual try-on, tone matching")

    st.markdown("""
    **How it works:** Four specialized AI agents, each backed by a different Crusoe model,
    collaborate on a complete beauty consultation, fed by a **live Perfect Corp skin-analysis call**.

    | Agent | Model | Role |
    |-------|-------|------|
    | Skin Analyst | DeepSeek V4 Pro | Reads the live skin metrics, flags issues |
    | Tone Expert | Llama 3.3 70B | Recommends foundation + palette from undertone |
    | Makeup Artist | Qwen3 235B | Suggests looks that complement the analysis |
    | Style Coordinator | Nemotron Nano 30B | Synthesizes everything into one routine |
    """)

    st.divider()

    pc_col1, pc_col2, pc_col3 = st.columns(3)
    with pc_col1:
        api_key_set = bool(os.environ.get("PERFECT_CORP_API_KEY", ""))
        if api_key_set:
            st.success("Perfect Corp API key configured (live)")
        else:
            st.warning("API key not set — runs in mock mode")
    with pc_col2:
        st.metric("Perfect Corp APIs", "50+", "Available")
    with pc_col3:
        st.metric("API Units", "1,000", "$179 value")

    st.divider()

    # --- Image source: upload OR bundled sample face ---
    st.markdown("##### 1. Choose a face image")
    BUNDLED_FACE = Path(__file__).parent / "sample_faces" / "test_face_tight.jpg"
    pc_up_col, pc_sample_col = st.columns([2, 1])
    with pc_up_col:
        uploaded = st.file_uploader("Upload your own photo (jpg/png, face filling >40% of frame)",
                                    type=["jpg", "jpeg", "png"], key="beauty_upload")
    with pc_sample_col:
        st.image(str(BUNDLED_FACE), caption="Bundled sample face", width=200)
        use_sample = st.checkbox("Use bundled sample face", value=not bool(uploaded), key="use_sample_face")

    # Resolve which bytes to use
    face_bytes: bytes | None = None
    face_source = ""
    if uploaded is not None and not use_sample:
        face_bytes = uploaded.read()
        face_source = uploaded.name
    elif BUNDLED_FACE.exists():
        face_bytes = BUNDLED_FACE.read_bytes()
        face_source = "demo/sample_faces/test_face_tight.jpg"

    st.divider()

    if st.button("💄 Run Beauty Consultation", type="primary", use_container_width=True):
        from colosseum.scenarios import BEAUTY_CONSULTATION
        from colosseum.perfect_corp_client import get_perfect_client

        # --- Step 1: Live skin analysis (if API key + face available) ---
        skin_summary = ""
        skin_overlay_metrics: list[tuple[str, bytes]] = []  # (metric_name, image_bytes)
        skin_scores: dict = {}

        if face_bytes and api_key_set:
            with st.spinner("📸 Running Perfect Corp skin analysis (live API call)..."):
                pc = get_perfect_client()
                analysis = pc.analyze_skin(face_bytes)

            if analysis.get("status") == "success":
                zip_url = (analysis.get("result") or {}).get("url", "")
                if zip_url:
                    with st.spinner("📊 Fetching analysis overlays..."):
                        assets = pc.fetch_skin_analysis_assets(zip_url)
                    if assets.get("status") == "success":
                        skin_scores = assets.get("scores", {})
                        # Display scorecard
                        st.success(f"✅ Live skin analysis complete — source: {face_source}")
                        score_cols = st.columns(5)
                        all_metrics = [(k, v) for k, v in skin_scores.items()
                                       if isinstance(v, dict) and "ui_score" in v]
                        for i, (metric, info) in enumerate(all_metrics[:10]):
                            with score_cols[i % 5]:
                                st.metric(metric.replace("_", " ").title(),
                                          f"{info.get('ui_score', 0)}/100")
                        # Overall + age
                        overall_col, age_col = st.columns(2)
                        with overall_col:
                            overall = skin_scores.get("all", {}).get("score", 0)
                            st.metric("Overall Skin Score", f"{overall}/100")
                        with age_col:
                            est_age = skin_scores.get("skin_age", None)
                            if est_age:
                                st.metric("Estimated Skin Age", f"{est_age}")

                        # Mask overlays — show the real ML output Perfect Corp generates
                        st.markdown("##### 2. Live ML overlays from Perfect Corp")
                        overlays = assets.get("overlays", {})
                        # Show 4 most interesting overlays in a row
                        priority = ["wrinkle", "pore", "acne", "redness", "texture",
                                    "age_spot", "moisture", "oiliness", "radiance", "dark_circle_v2"]
                        shown = [(m, overlays[m]) for m in priority if m in overlays][:4]
                        if shown:
                            ov_cols = st.columns(len(shown))
                            for i, (metric, img_bytes) in enumerate(shown):
                                with ov_cols[i]:
                                    st.image(img_bytes,
                                             caption=f"{metric.replace('_',' ').title()} detection",
                                             use_container_width=True)
                            skin_overlay_metrics = shown

                        # Build summary that the agents can reason over
                        score_lines = [f"{k}: {v.get('ui_score','?')}/100"
                                       for k, v in all_metrics]
                        skin_summary = (
                            f"Live Perfect Corp skin analysis results:\n"
                            f"Overall score: {overall}/100, estimated skin age: {est_age}.\n"
                            f"Per-metric scores: {', '.join(score_lines)}."
                        )
                    else:
                        st.warning(
                            "Skin analysis ran but overlays could not be parsed. "
                            "Agents will proceed with the consultation using general advice."
                        )
                else:
                    st.warning("Skin analysis returned no result URL. Continuing with mock advice.")
            else:
                msg = str(analysis.get("message", ""))[:200]
                if "error_src_face_too_small" in msg or "face_too_small" in msg:
                    st.info(
                        "Perfect Corp couldn't detect a large-enough face in the uploaded image — "
                        "the bundled sample face works as a fallback. Continuing with the agent consultation."
                    )
                else:
                    st.info(
                        "Live skin analysis unavailable for this image — "
                        "agents will continue the consultation with general advice. "
                        f"({msg[:120]})"
                    )
        elif not api_key_set:
            st.info("PERFECT_CORP_API_KEY not set — running consultation in mock mode with simulated skin scores.")
        st.divider()

        if demo_mode:
            client = MockCrusoeClient(latency_range=(0.5, 1.5))
        else:
            from colosseum.crusoe_client import CrusoeClient
            client = CrusoeClient()

        from colosseum.simulation.orchestrator import Orchestrator
        orch = Orchestrator(client=client)

        # Inject the live skin analysis into the scenario so agents reason over real data
        config = BEAUTY_CONSULTATION.model_copy(deep=True)
        if skin_summary:
            config.environment_prompt = config.environment_prompt + "\n\n" + skin_summary
        st.subheader(f"💄 {config.name}")
        st.caption(f"**Host:** Nemotron Super 120B | **Task:** {config.task}")

        # Agent cards with their model avatars
        cols = st.columns(len(config.agents))
        for i, ag in enumerate(config.agents):
            with cols[i]:
                ag_av = avatar_path_for(ag.model)
                if ag_av:
                    st.image(str(ag_av), use_container_width=True)
                has_tools = "🔧" if ag.tools else ""
                tool_count = f"{len(ag.tools)} tools" if ag.tools else "no tools"
                st.markdown(f"""
                <div style="border: 2px solid #E91E63; border-radius: 10px; padding: 10px; margin: 5px 0;">
                    <strong>{has_tools} {ag.name}</strong><br>
                    <small style="color: #E91E63;">{ag.role.value}</small><br>
                    <small>{ag.personality[:60]}</small><br>
                    <small style="color: #888;">{tool_count}</small>
                </div>
                """, unsafe_allow_html=True)

        beauty_bar = st.progress(0)
        beauty_status = st.empty()

        def update(step: int, total: int) -> None:
            beauty_bar.progress(min(step / total, 1.0))
            beauty_status.text(f"💄 Step {step}/{total} — Beauty agents consulting...")

        start_time = time.time()
        result = orch.run_experiment(config, progress_callback=update)
        elapsed = time.time() - start_time

        beauty_bar.progress(1.0)
        beauty_status.text(f"✅ Consultation complete in {elapsed:.1f}s — {result.total_steps} steps")

        st.subheader("💬 Consultation Timeline")
        for step_idx, step_actions in enumerate(result.steps):
            with st.expander(f"Step {step_idx + 1} — {len(step_actions)} actions", expanded=step_idx < 3):
                for action in step_actions:
                    is_tool = "TOOL_CALL" in action.content or action.action_type == "tool_call"
                    icon = "🔧" if is_tool else "💬"
                    color = "violet" if is_tool else "green"
                    st.markdown(
                        f":{color}[{icon} **{action.agent_name}** [{action.action_type}]"
                        f": {action.content[:300]}]"
                    )

        # Agent stats
        st.subheader("📊 Agent Performance")
        stats_data = []
        for name, s in result.agent_stats.items():
            stats_data.append({
                "Agent": name, "Role": s.get("role", "-"),
                "Steps": s.get("steps_taken", 0), "State": s.get("state", "-"),
            })
        st.dataframe(stats_data, use_container_width=True, hide_index=True)

        st.success(
            "Perfect Corp Challenge: Multi-agent AI system using Perfect Corp APIs "
            "for immersive consumer beauty experiences — skin analysis, virtual try-on, "
            "and personalized recommendations."
        )

    st.divider()
    st.caption("Perfect Corp integration for DevNetwork AI+ML Hackathon 2026")
    st.caption("APIs: AI Skin Analysis | AI Skin Tone | AI Makeup VTO | AI Fashion VTO | AI Hair VTO")


# =============================================================================
# TAB 4: Talk to the Catalog — Perfect Corp avatars + live Crusoe chat
# =============================================================================
with tab_avatar:
    st.subheader("🎭 Talk to the Catalog")
    st.caption(
        "Every Crusoe model has its own AI-generated character — visual identities "
        "created live by Perfect Corp's text-to-image API. Pick a model. Talk to it. "
        "Replies come from the real Crusoe inference endpoint, in that model's voice."
    )

    # subtle CSS for the avatar "alive" feel
    st.markdown("""
    <style>
      .avatar-card {
        border: 2px solid #2C3E50; border-radius: 14px; padding: 10px;
        text-align: center; background: rgba(0,0,0,0.02);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
      }
      .avatar-card:hover { transform: translateY(-3px); }
      @keyframes breathe { 0%,100% { transform: scale(1); } 50% { transform: scale(1.012); } }
      .avatar-live img { animation: breathe 4s ease-in-out infinite; border-radius: 14px; }
      .avatar-glow { box-shadow: 0 0 22px var(--glow); border-color: var(--glow); }
    </style>
    """, unsafe_allow_html=True)

    # --- Gallery vs. selected ---
    selected = st.session_state.avatar_selected
    if selected is None:
        st.markdown("##### Choose your model")
        # 7 avatars in a responsive grid (4 cols → 3 wrap)
        rows = [MODEL_AVATARS[:4], MODEL_AVATARS[4:]]
        for row in rows:
            cols = st.columns(len(row))
            for i, av in enumerate(row):
                img_path = AVATAR_DIR / f"{av['file']}.jpg"
                with cols[i]:
                    if img_path.exists():
                        st.image(str(img_path), use_container_width=True)
                    st.markdown(
                        f"<div style='text-align:center'>"
                        f"<strong>{av['name']}</strong><br>"
                        f"<small style='color:{av['color']}'>{av['role']}</small><br>"
                        f"<small>{av['tagline']}</small>"
                        f"</div>",
                        unsafe_allow_html=True,
                    )
                    if st.button(f"Talk to {av['name'].split()[0]}",
                                 key=f"select_{av['file']}",
                                 use_container_width=True):
                        st.session_state.avatar_selected = av['model_id']
                        st.rerun()
    else:
        av = MODEL_AVATARS_BY_ID.get(selected)
        if av is None:
            st.session_state.avatar_selected = None
            st.rerun()

        col_avatar, col_chat = st.columns([1, 2])

        with col_avatar:
            img_path = AVATAR_DIR / f"{av['file']}.jpg"
            if img_path.exists():
                st.markdown(
                    f"<div class='avatar-live' style='--glow:{av['color']}'>",
                    unsafe_allow_html=True,
                )
                st.image(str(img_path), use_container_width=True)
                st.markdown("</div>", unsafe_allow_html=True)
            st.markdown(f"### {av['name']}")
            st.markdown(f"<span style='color:{av['color']}'><strong>{av['role']}</strong></span>",
                        unsafe_allow_html=True)
            st.caption(av['tagline'])
            st.caption(f"Model ID: `{av['model_id']}`")

            if st.button("← Back to gallery", use_container_width=True):
                st.session_state.avatar_selected = None
                st.rerun()
            if st.button("🗑️ Clear chat", use_container_width=True):
                st.session_state.avatar_chat_history[selected] = []
                st.rerun()

        with col_chat:
            history = st.session_state.avatar_chat_history.setdefault(selected, [])

            # render history
            chat_area = st.container(height=420)
            with chat_area:
                if not history:
                    st.info(f"Say hi to **{av['name']}**. Replies route through Crusoe Managed Inference.")
                for msg in history:
                    with st.chat_message(msg["role"]):
                        st.markdown(msg["content"])

            # input
            user_msg = st.chat_input(f"Message {av['name']}...")
            if user_msg:
                history.append({"role": "user", "content": user_msg})

                # Dispatch to Crusoe (live) or Mock
                api_key = os.environ.get("CRUSOE_API_KEY", "")
                if api_key:
                    from colosseum.crusoe_client import CrusoeClient
                    client = CrusoeClient()
                    use_live = True
                else:
                    client = MockCrusoeClient(latency_range=(0.4, 1.0))
                    use_live = False

                system_prompt = (
                    f"You are {av['name']}, an AI character represented by a Perfect Corp-generated "
                    f"avatar. Your role: {av['role']}. Your style: {av['tagline']}\n\n"
                    "Stay in character. Be concise (1-3 short paragraphs). "
                    "If asked who you are, mention you're powered by your specific model "
                    "running on Crusoe Cloud Managed Inference."
                )

                # only send last few messages to keep token budget tight
                msgs = [{"role": "system", "content": system_prompt}]
                for m in history[-8:]:
                    msgs.append({"role": m["role"], "content": m["content"]})

                with chat_area:
                    with st.chat_message("user"):
                        st.markdown(user_msg)
                    with st.chat_message("assistant"):
                        placeholder = st.empty()
                        placeholder.markdown("_thinking..._")
                        try:
                            resp = client.chat(
                                messages=msgs,
                                model=av["model_id"],
                                temperature=0.7,
                                max_tokens=512,
                                timeout=30.0,
                            )
                            reply = resp.get("content", "").strip()
                            if not reply:
                                reply = "_(empty response — try again)_"
                            placeholder.markdown(reply)
                            history.append({"role": "assistant", "content": reply})
                        except Exception as e:
                            placeholder.error(f"Crusoe API error: {e}")
                            history.append({"role": "assistant",
                                            "content": f"⚠️ Error: {e}"})

                st.session_state.avatar_chat_history[selected] = history
                badge = "🟢 Live Crusoe" if use_live else "🟡 Offline mock"
                st.caption(f"{badge} · model: {av['name']}")

    st.divider()
    st.caption("Perfect Corp × Crusoe — avatars generated live, conversation routed to real model APIs.")
