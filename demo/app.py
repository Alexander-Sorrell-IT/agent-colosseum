"""Streamlit demo dashboard for Agent Colosseum."""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from colosseum.scenarios import ALL_SCENARIOS
from colosseum.mock_client import MockCrusoeClient

st.set_page_config(
    page_title="Agent Colosseum",
    page_icon="🏛️",
    layout="wide",
)

# --- Session init ---
for key, default in {
    "results": [],
    "active_config": None,
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# --- Header ---
col_title, col_badges = st.columns([3, 1])
with col_title:
    st.title("🏛️ Agent Colosseum")
    st.caption("Simulate multi-agent environments with Nvidia Nemotron on Crusoe Cloud")
with col_badges:
    st.markdown("![Nvidia Nemotron](https://img.shields.io/badge/Nemotron-Super%20120B-76B900?style=flat&logo=nvidia)")
    st.markdown("![Crusoe Cloud](https://img.shields.io/badge/Crusoe-Managed%20Inference-FF6B00?style=flat)")

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

# --- Main area ---
if run_btn:
    # Initialize client
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

    # --- Experiment header ---
    st.subheader(f"🧪 {config.name}")
    st.caption(f"**Task:** {config.task}")

    # Agent cards
    cols = st.columns(len(config.agents))
    for i, ag in enumerate(config.agents):
        with cols[i]:
            role_colors = {
                "worker": "#4CAF50",
                "critic": "#FF9800",
                "coordinator": "#2196F3",
                "observer": "#9C27B0",
                "orchestrator": "#F44336",
            }
            color = role_colors.get(ag.role.value, "#757575")
            st.markdown(f"""
            <div style="border: 2px solid {color}; border-radius: 10px; padding: 10px; margin: 5px 0;">
                <strong>{ag.name}</strong><br>
                <small style="color: {color};">{ag.role.value}</small><br>
                <small>{ag.personality[:60] if ag.personality else '—'}</small>
            </div>
            """, unsafe_allow_html=True)

    # --- Run ---
    progress_bar = st.progress(0)
    status_text = st.empty()
    action_area = st.empty()

    live_actions = []

    def update(step: int, total: int) -> None:
        progress_bar.progress(min(step / total, 1.0))
        status_text.text(f"⚡ Step {step}/{total} — Nemotron agents interacting...")
        if hasattr(update, "last_actions"):
            live_actions.extend(update.last_actions)

    update.last_actions = []

    start_time = time.time()
    result = orch.run_experiment(config, progress_callback=update)
    elapsed = time.time() - start_time

    st.session_state.results.append(result)

    progress_bar.progress(1.0)
    status_text.text(f"✅ Complete in {elapsed:.1f}s — {result.total_steps} steps run")
    st.caption(f"Model: {orch.stats.get('orchestrator_model', 'Nemotron')} | "
               f"API calls: {orch.stats['calls']} | "
               f"Avg latency: {orch.stats.get('avg_latency_ms', 0):.0f}ms")

    # --- Agent Stats ---
    st.subheader("📊 Agent Performance")
    stats_data = []
    for name, s in result.agent_stats.items():
        stats_data.append({
            "Agent": name,
            "Role": s.get("role", "-"),
            "Steps": s.get("steps_taken", 0),
            "State": s.get("state", "-"),
        })
    st.dataframe(stats_data, use_container_width=True, hide_index=True)

    # --- Interaction Timeline ---
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

    # --- Anomalies ---
    if result.anomalies:
        st.subheader("⚠️ Anomalies Detected")
        for a in result.anomalies:
            st.error(a)

    # --- AI Analysis ---
    if analyze:
        st.subheader("🧠 Orchestrator Analysis")
        with st.spinner("Analyzing results with Nemotron Super-120B..."):
            analysis = orch.analyze_results(result)
        st.info(analysis)

    st.divider()

# --- Comparison ---
if len(st.session_state.results) > 1:
    st.subheader("🔬 Cross-Experiment Comparison")
    if st.button("Compare All Experiments"):
        from colosseum.simulation.orchestrator import Orchestrator
        orch = Orchestrator()
        orch.results = st.session_state.results
        with st.spinner("Comparing experiments..."):
            comparison = orch.compare_experiments()
        st.info(comparison)
