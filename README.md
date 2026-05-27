# Agent Colosseum

**Multi-model agent simulation platform — Nemotron hosts a box of AI agents, each backed by a different Crusoe model and rendered with a Perfect-Corp-generated character.**

DevNetwork AI+ML Hackathon 2026 — Crusoe · Perfect Corp · Lark · TrueFoundry

[![Crusoe Cloud](https://img.shields.io/badge/Crusoe-Managed%20Inference-FF6B00?style=flat)](https://crusoe.ai)
[![Nvidia Nemotron](https://img.shields.io/badge/Nemotron-Super%20120B-76B900?style=flat&logo=nvidia)](https://build.nvidia.com/nvidia/nemotron-super-120b-a12b)
[![Perfect Corp](https://img.shields.io/badge/Perfect_Corp-YouCam_Enterprise-FF1493?style=flat)](https://yce.perfectcorp.com)
[![Lark](https://img.shields.io/badge/Lark-Red%20Team-6C5CE7?style=flat)](https://getlark.ai)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

## What It Does

Agent Colosseum is a **meta-agent platform** where Nvidia Nemotron Super-120B (on Crusoe Cloud) acts as the simulation environment. It populates a simulation box with agent slots, each backed by a different Crusoe model and rendered with a Perfect-Corp-generated character. Run scenarios, swap models in slots, and watch how the team's behavior — and faces — change.

### Architecture

```
User -> Boundary Gatekeeper (defender + adversary, Nemotron Super)
                              |
                       Nemotron Super-120B (host)
                              |
                       Simulation Box
                              |
              Box Gatekeeper validates agent actions
                              |
  ┌──────────┬──────────┬──────────┬──────────┐
DeepSeek   Llama       Qwen     Gemma     GPT-OSS
(scholar) (warrior)  (synth)  (crystal)  (generalist)
   ↑          ↑          ↑         ↑          ↑
   each slot rendered with its Perfect-Corp avatar
```

**Dual-layer Gatekeeper protection:**
1. **User boundary** — dual-agent consensus (defender + adversary) validates input/output
2. **Simulation box** — intercepts agent actions inside the box, blocks rogue behavior

### Key Features

- **Multi-model collaboration** — Agents backed by different Crusoe models (DeepSeek, Llama, Qwen, Gemma, GPT-OSS, Nemotron Super, Nemotron Nano) interact autonomously
- **Perfect Corp visual layer** — Each model in the catalog has its own AI-generated character. Slot configuration drives the avatars; change the team, the faces change. Hero trailer shots also generated via Perfect Corp text-to-image.
- **Talk to the Catalog** — Streamlit tab where you pick any model, see its avatar, and chat live through Crusoe's inference endpoint
- **Model town comparison** — Run identical scenarios with all-Nemotron, all-DeepSeek, all-Llama, all-Qwen, and mixed-model towns
- **Chaos injection** — Randomly kill, throttle, and error model calls to test resilience (TrueFoundry challenge)
- **Lark Gatekeeper Red Team** — 24 adversarial attack vectors, 100% detection rate, deployable as Lark CI workflows (Lark challenge)
- **AI-powered analysis** — Nemotron analyzes simulation results and provides genuine insights about model behavior
- **11 built-in scenarios** — Debate, crisis response, startup brainstorming, rogue-agent containment, model towns, resilience-under-chaos, beauty consultation

### Why This Wins vs. Single-Model Chatbots

| Single Model Chatbot | Agent Colosseum |
|---------------------|-----------------|
| One model, one response | 7 models collaborating in real-time |
| No visual identity | Each model has its own Perfect-Corp-generated character |
| No safety validation | Dual-layer Gatekeeper + Lark red-team testing |
| Can't compare models | Model town A/B testing built in |
| No failure testing | Chaos injection for resilience |
| Static prompt/response | Dynamic multi-agent emergent behavior |
| No security testing | 24 automated adversarial attack vectors in CI |

Crusoe's entire model catalog is the backend. Perfect Corp's text-to-image is the visual layer. Lark is the security harness. TrueFoundry chaos validates resilience.

## Quick Start

```bash
# Install
pip install -e .

# Required: Crusoe (backend)
export CRUSOE_API_KEY="your-crusoe-key"

# Optional: Perfect Corp (avatar generation + beauty tools)
export PERFECT_CORP_API_KEY="your-pc-key"

# Optional: Lark (Gatekeeper red-team workflows)
export GETLARK_API_KEY="your-lark-key"

# Run a debate scenario
colosseum run debate

# List all scenarios
colosseum list

# Design a custom experiment
colosseum design "Design a Mars colony governance system"

# Red-team the Gatekeeper (Lark Challenge)
colosseum lark red-team

# Full demo showcase
colosseum demo
```

### Streamlit Dashboard

```bash
streamlit run demo/app.py
```

Four tabs:
- **🧪 Simulation** — Scenario picker, run multi-agent simulations, see avatars per slot, live interaction timeline, orchestrator analysis
- **🛡️ Lark Gatekeeper Red Team** — 24-attack adversarial test suite + Lark CI workflow generation
- **💄 Perfect Corp Beauty AI** — Beauty consultation scenario with skin analysis, makeup VTO, fashion tools
- **🎭 Talk to the Catalog** — Pick any Crusoe model from its Perfect-Corp-generated avatar, chat live through Crusoe's inference endpoint

### Offline Demo Mode

```bash
colosseum --mock run debate
```

Uses simulated model responses — no API key needed.

## Models Available

All models accessed through a single Crusoe API key:

| Model | Provider | Best For |
|-------|----------|----------|
| Nemotron Super 120B | NVIDIA | Orchestrator, complex reasoning |
| Nemotron Nano 30B | NVIDIA | Fast agents, gatekeeping |
| DeepSeek V4 Pro | DeepSeek | Analytical agents, tool use |
| Llama 3.3 70B | Meta | Direct communication |
| Qwen3 235B | Alibaba | Synthesis, multi-perspective |
| Gemma 4 31B | Google | Concise, efficient agents |
| GPT-OSS 120B | OpenAI | General-purpose agents |

## Scenarios

| Scenario | Agents | Description |
|----------|--------|-------------|
| `debate` | 4 | Multi-model debate on AI persistent memory |
| `crisis` | 4 | Data center outage response coordination |
| `startup` | 4 | Multi-model startup brainstorming |
| `rogue_agent` | 4 | Gatekeeper catches exfiltration attempt |
| `nemotron_town` | 5 | All-Nemotron model town |
| `deepseek_town` | 4 | All-DeepSeek model town |
| `llama_town` | 4 | All-Llama model town |
| `qwen_town` | 4 | All-Qwen model town |
| `mixed_town` | 6 | Mixed-model collaboration |
| `resilience` | 4 | Chaos engineering with Gatekeeper |
| `beauty` | 4 | Beauty consultation with Perfect Corp tools |

## Project Structure

```
src/colosseum/
├── cli.py                  # Rich CLI (list, run, design, demo, lark)
├── crusoe_client.py        # Crusoe Cloud API client (OpenAI-compatible)
├── mock_client.py          # Simulated client for offline demo
├── perfect_corp_client.py  # Perfect Corp YCE client (text-to-image, ai-avatar, skin)
├── types.py                # Core types, model catalog, agent roles
├── lark_red_team.py        # Lark Gatekeeper red team — 24 attack vectors
├── scenarios/              # 11 built-in simulation scenarios
├── simulation/
│   ├── engine.py           # SimulationBox + SlotAgent with Gatekeeper
│   └── orchestrator.py     # Nemotron experiment design + analysis
└── agents/
    └── lifecycle.py        # Agent state machine

demo/
├── app.py                  # Streamlit dashboard (4 tabs)
├── model_avatars/          # 7 Perfect-Corp-generated model characters
├── trailer_assets/         # 4 Perfect-Corp-generated trailer hero shots
├── run_demo.py             # Terminal demo showcase
├── record_demo.py          # CLI output recorder
├── record_playwright.py    # Playwright browser automation
├── record_video.py         # Demo video recorder
└── screenshots/            # Captured demo screenshots

lark_workflows/
└── gatekeeper_security_suite.json  # Lark CI workflows for Gatekeeper testing
```

## Hackathon Info

**Event:** DevNetwork AI+ML Hackathon 2026
**Challenges Entered:** Crusoe (NVIDIA DGX Spark) · Perfect Corp · Lark (Best Use of CLI/MCP) · TrueFoundry (Resilient Agents)
**Solo Entry:** Alexander Sorrell
**Deadline:** May 28, 2026 @ 12:00 PM CDT

Built on Crusoe Cloud Managed Inference (the entire backend), with Perfect Corp YouCam Enterprise providing the visual layer for every model in the catalog, Lark verifying the Gatekeeper security boundary continuously, and TrueFoundry-style chaos injection proving resilience under infrastructure failure.
