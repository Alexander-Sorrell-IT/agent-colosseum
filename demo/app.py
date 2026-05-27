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
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

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
tab_sim, tab_lark, tab_perfect = st.tabs([
    "🧪 Simulation", "🛡️ Lark Gatekeeper Red Team", "💄 Perfect Corp Beauty AI",
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
        st.caption(f"**Host:** {host_label} manages this simulation | **Task:** {config.task}")

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
    collaborate on a complete beauty consultation. Each agent calls **real Perfect Corp APIs**
    as tools during the simulation.

    | Agent | Model | Perfect Corp API |
    |-------|-------|-----------------|
    | Skin Analyst | DeepSeek V4 Pro | AI Skin Analysis — texture, moisture, pores, wrinkles, acne |
    | Tone Expert | Llama 3.3 70B | AI Skin Tone Analysis — undertone, season, foundation match |
    | Makeup Artist | Qwen3 235B | AI Makeup VTO — virtual try-on with realistic rendering |
    | Style Coordinator | Nemotron Nano 30B | Synthesizes all results into complete look |
    """)

    st.divider()

    pc_col1, pc_col2, pc_col3 = st.columns(3)
    with pc_col1:
        api_key_set = bool(os.environ.get("PERFECT_CORP_API_KEY", ""))
        if api_key_set:
            st.success("Perfect Corp API key configured")
        else:
            st.warning("API key not set — uses simulated results")
    with pc_col2:
        st.metric("Perfect Corp APIs", "50+", "Available")
    with pc_col3:
        st.metric("API Units", "1,000", "$179 value")

    st.divider()

    if st.button("💄 Run Beauty Consultation", type="primary", use_container_width=True):
        from colosseum.scenarios import BEAUTY_CONSULTATION

        if demo_mode:
            client = MockCrusoeClient(latency_range=(0.5, 1.5))
        else:
            from colosseum.crusoe_client import CrusoeClient
            client = CrusoeClient()

        from colosseum.simulation.orchestrator import Orchestrator
        orch = Orchestrator(client=client)

        config = BEAUTY_CONSULTATION
        st.subheader(f"💄 {config.name}")
        st.caption(f"**Host:** Nemotron Super 120B | **Task:** {config.task}")

        # Agent cards
        cols = st.columns(len(config.agents))
        for i, ag in enumerate(config.agents):
            with cols[i]:
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
