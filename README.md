# Agent Colosseum

**Multi-model agent simulation platform — Nemotron orchestrates a box of AI agents backed by 7 different Crusoe models.**

DevNetwork AI+ML Hackathon 2026 — Crusoe Challenge

[![Crusoe Cloud](https://img.shields.io/badge/Crusoe-Managed%20Inference-FF6B00?style=flat)](https://crusoe.ai)
[![Nvidia Nemotron](https://img.shields.io/badge/Nemotron-Super%20120B-76B900?style=flat&logo=nvidia)](https://build.nvidia.com/nvidia/nemotron-super-120b-a12b)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

## What It Does

Agent Colosseum is a **meta-agent platform** where Nvidia Nemotron (Super-120B on Crusoe Cloud) acts as the simulation environment. It creates simulation boxes, populates them with agent slots backed by different AI models, runs collaborative scenarios, and produces comparative analysis.

### Architecture

```
User -> Gatekeeper (boundary) -> Orchestrator (Nemotron) -> Simulation Box
                                                               |
                                           Gatekeeper (box) <- validates agent actions
                                                               |
                                           Agent Slots (7 models via Crusoe)
```

**Dual-layer Gatekeeper protection:**
1. **User boundary** — validates all input/output between user and system
2. **Simulation box** — intercepts agent actions inside the box, blocks rogue behavior

### Key Features

- **Multi-model collaboration** — Agents backed by different Crusoe models (DeepSeek, Llama, Qwen, Gemma, GPT-OSS, Nemotron) interact autonomously
- **Model town comparison** — Run identical scenarios with all-Nemotron, all-DeepSeek, all-Llama, all-Qwen, and mixed-model towns to compare performance
- **Chaos injection** — Randomly kill, throttle, and error model calls to test resilience (TrueFoundry challenge)
- **AI-powered analysis** — Nemotron analyzes simulation results and provides genuine insights about model behavior
- **10 built-in scenarios** — Debate, crisis response, startup brainstorming, rogue agent containment, model towns, and resilience testing

### Why This Wins vs. Single-Model Chatbots

| Single Model Chatbot | Agent Colosseum |
|---------------------|-----------------|
| One model, one response | 7 models collaborating in real-time |
| No safety validation | Dual-layer Gatekeeper protection |
| Can't compare models | Model town A/B testing built in |
| No failure testing | Chaos injection for resilience |
| Static prompt/response | Dynamic multi-agent emergent behavior |

Crusoe's entire model catalog is the backend — not just one model.

## Quick Start

```bash
# Install
pip install -e .

# Set your Crusoe API key
export CRUSOE_API_KEY="your-key-here"

# Run a debate scenario
colosseum run debate

# List all scenarios
colosseum list

# Design a custom experiment
colosseum design "Design a Mars colony governance system"

# Full demo showcase
colosseum demo
```

### Streamlit Dashboard

```bash
streamlit run demo/app.py
```

Opens an interactive dashboard with:
- Scenario selection and custom experiment design
- Live agent interaction timeline
- Agent performance stats
- Orchestrator AI analysis
- Cross-experiment comparison

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

## Project Structure

```
src/colosseum/
├── cli.py                  # Rich CLI (list, run, design, demo)
├── crusoe_client.py        # Crusoe Cloud API client (OpenAI-compatible)
├── mock_client.py          # Simulated client for offline demo
├── types.py                # Core types, model catalog, agent roles
├── scenarios/              # 10 built-in simulation scenarios
├── simulation/
│   ├── engine.py           # SimulationBox + SlotAgent with Gatekeeper
│   └── orchestrator.py     # Nemotron experiment design + analysis
└── agents/
    └── lifecycle.py        # Agent state machine

demo/
├── app.py                  # Streamlit dashboard
├── run_demo.py             # Terminal demo showcase
├── record_demo.py          # CLI output recorder
├── record_playwright.py    # Playwright browser automation
└── screenshots/            # Captured demo screenshots
```

## Hackathon Info

**Event:** DevNetwork AI+ML Hackathon 2026
**Challenge:** Crusoe Cloud — Build with Crusoe Managed Inference
**Prize:** NVIDIA DGX Spark
**Solo Entry:** Alexander Sorrell
**Deadline:** May 28, 2026 @ 12:00 PM CDT

Built entirely on Crusoe Cloud Managed Inference. Zero external API dependencies — one API key, seven models, infinite possibilities.
