# Agent Colosseum — Multi-Model Agent Simulation Platform

## Tagline
Nemotron Super-120B orchestrates a simulation box where 7 different Crusoe models collaborate, compete, and get tested — with dual-layer Gatekeeper protection.

## Elevator Pitch (140 chars)
One API key. Seven Crusoe models. Infinite agent combinations. Nemotron runs the show — designs experiments, spawns model-backed agents, and analyzes who works best together.

## About the Project

### What It Does

Agent Colosseum is a **meta-agent platform** where Nvidia Nemotron (Super-120B on Crusoe Cloud) acts as the entire simulation environment. It's not a chatbot — it's a simulation engine.

1. **Orchestrator (Nemotron)** designs multi-agent experiments, assigns different Crusoe models to each agent slot based on their strengths, and spawns a simulation box
2. **Simulation Box** runs the scenario — agents backed by DeepSeek, Llama, Qwen, Gemma, GPT-OSS, and Nemotron models interact autonomously, step by step
3. **Dual-layer Gatekeeper** protects the user/system boundary AND intercepts agent actions inside the box, blocking rogue behavior
4. **Orchestrator analyzes** the results — comparing how different models performed, what emergent behaviors appeared, and who collaborated best

### The Problem It Solves

When you're building with AI models, you face real questions:
- Which model is best for my use case?
- How do different models work together on a team?
- What happens when models fail mid-task?
- Is my multi-agent system safe?

Single-model chatbots can't answer these. Agent Colosseum can — because it runs the models against each other and measures what happens.

### Key Features

**Model Town Comparison** — Run identical scenarios with all-Nemotron, all-DeepSeek, all-Llama, all-Qwen, and mixed-model agent teams. See which model combination produces the best collaboration, fewest failures, and most coherent output.

**Chaos Injection** — Randomly kill, throttle, and error model calls mid-simulation. Test which model combinations survive failures and which cascade-collapse. This stretches into the TrueFoundry "Resilient Agents" challenge.

**10 Built-in Scenarios** — Debate, crisis response, startup brainstorming, rogue agent containment, 4 single-model towns, mixed-model town, and resilience chaos testing.

**Streamlit Dashboard** — Interactive UI for designing experiments, watching agent interactions in real-time, viewing performance stats, and reading Nemotron's AI analysis.

**Rich CLI** — Terminal-based control with `list`, `run`, `design`, and `demo` commands. Offline mock mode available for demos without an API key.

### Architecture

```
User → Gatekeeper (boundary) → Orchestrator (Nemotron Super-120B)
                                        │
                                  Simulation Box
                                        │
                    Gatekeeper (box) ─── validates agent actions
                                        │
                    ┌───────────────────┼───────────────────┐
                    │         │         │         │         │
                 DeepSeek   Llama     Qwen     Gemma   GPT-OSS
                   slot      slot      slot      slot     slot
```

### Why Crusoe?

Crusoe Cloud Managed Inference is the entire backend. One API key gives access to 7 production models through an OpenAI-compatible endpoint. No external APIs. No model hosting. No GPU management. Just one endpoint, infinite model combinations.

This project proves why Crusoe's full model catalog matters — you can't do multi-model comparison with a single model provider.

### How We Built It

- **Backend:** Python, Crusoe Cloud Managed Inference API (OpenAI-compatible)
- **Orchestrator:** Nvidia Nemotron Super-120B for experiment design and analysis
- **Agent Models:** DeepSeek V4 Pro, Llama 3.3 70B, Qwen3 235B, Gemma 4 31B, GPT-OSS 120B, Nemotron Nano 30B
- **Gatekeeper:** Nemotron Nano 30B for fast safety validation
- **Frontend:** Streamlit dashboard with real-time agent interaction timeline
- **CLI:** Rich terminal UI with progress spinners and formatted output
- **Testing:** 197 live API calls across all components, 0 errors

### What's Next

- Persistent simulation history and replay
- Custom scenario builder UI
- Agent memory across simulation runs
- Real-time collaboration between multiple human users and AI agents
- Integration with Crusoe's upcoming features

### Try It Yourself

```bash
git clone https://github.com/Alexander-Sorrell-IT/agent-colosseum
cd agent-colosseum
pip install -e .
export CRUSOE_API_KEY="your-key"
colosseum demo
```

## Built With
- Crusoe Cloud Managed Inference
- Nvidia Nemotron (Super-120B, Nano-30B)
- DeepSeek V4 Pro
- Meta Llama 3.3 70B
- Alibaba Qwen3 235B
- Google Gemma 4 31B
- OpenAI GPT-OSS 120B
- Streamlit
- Python

## Challenges Entered
- Crusoe Cloud Challenge (Primary — NVIDIA DGX Spark)
- TrueFoundry Resilient Agent Challenge (Chaos injection testing)
